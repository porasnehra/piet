from typing import TypedDict, List, Dict, Any, Optional
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from app.config import GOOGLE_API_KEY, GEMINI_MODEL


# Define Graph State
class BreakdownState(TypedDict):
    messages: List[Dict[str, str]]
    query: str
    is_car_related: bool
    urgency: str
    diagnosis: str
    response: str


def get_llm():
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )


def extract_text(content: Any) -> str:
    """Safely extracts a single clean string from LangChain content response."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", item)))
            else:
                parts.append(str(item))
        return "\n".join(parts).strip()
    return str(content)


# 1. Guardrail Classifier Node
def guardrail_node(state: BreakdownState) -> Dict[str, Any]:
    """
    Evaluates whether the user's query is strictly related to cars, vehicles,
    automobile components, vehicle breakdowns, roadside emergencies, or in-cabin issues.
    If the query is unrelated (e.g. general questions, coding, recipes, casual chat),
    it is marked as out-of-scope to stop off-topic replies immediately.
    """
    llm = get_llm()
    query = state["query"]

    guardrail_prompt = f"""You are a strict safety classifier for "CypherPunks Emergency Vehicle & Roadside Assistance AI".
Your job is to determine whether the user's message is related to:
- Cars, automobiles, two-wheelers/bikes, trucks, or any motor vehicles
- Vehicle breakdowns, mechanical, electrical, or engine problems
- In-vehicle issues (AC, electronics, dashboard warning lights, strange noises, smoke, leaks, odors)
- Roadside emergencies (stranded driver, flat tire, dead battery, low fuel, towing, jumpstarting)
- Driving safety, highway breakdown protocols, vehicle maintenance, or automotive mechanics.

If the user query IS related to any of the above, mark it as IN-SCOPE.
If the query is asking about unrelated topics (such as general knowledge, coding, politics, recipes, homework, movies, philosophy, personal life, or random off-topic chatter), mark it as OUT-OF-SCOPE.

User Message: "{query}"

Respond with ONLY a valid JSON object in this format:
{{"is_car_related": true or false, "reason": "brief reason"}}
"""

    try:
        response = llm.invoke([SystemMessage(content="You are a strict JSON classifier."), HumanMessage(content=guardrail_prompt)])
        content = extract_text(response.content).strip()

        # Clean markdown backticks if any
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        data = json.loads(content.strip())
        is_car = bool(data.get("is_car_related", False))
    except Exception as e:
        # Fallback keyword inspection if API fails or output wasn't clean JSON
        keywords = ["car", "vehicle", "engine", "tyre", "tire", "brake", "battery", "oil", 
                    "coolant", "radiator", "gear", "clutch", "fuel", "smoke", "noise", 
                    "overheat", "stranded", "mechanic", "roadside", "highway", "breakdown", 
                    "steering", "headlight", "wiper", "horn", "puncture", "ac", "spark", "transmission"]
        is_car = any(kw in query.lower() for kw in keywords)

    return {"is_car_related": is_car}


# 2. Out-of-Scope Responder Node
def out_of_scope_node(state: BreakdownState) -> Dict[str, Any]:
    """
    Politely and firmly refuses to answer non-vehicle questions, adhering strictly
    to the requirement: 'if they ask any other query they stop it to replying'.
    """
    refusal_message = (
        "⛔ **Out of Scope Request**\n\n"
        "I am the **CypherPunks AI Roadside Assistance & Vehicle Emergency Assistant**.\n\n"
        "My system is exclusively trained to assist stranded drivers and resolve **car problems, in-vehicle faults, mechanical breakdowns, and roadside emergencies**.\n\n"
        "I cannot assist with general knowledge, coding, or non-vehicle queries.\n\n"
        "👉 *If you are experiencing any car issue (e.g., flat tyre, overheating engine, battery jumpstart, weird sound, warning lights), please describe your vehicle symptoms and I will help you immediately.*"
    )
    return {
        "response": refusal_message,
        "urgency": "OUT_OF_SCOPE",
        "diagnosis": "Non-car query blocked by guardrails."
    }


# 3. Vehicle Diagnostics & Roadside Triage Node
def diagnostic_node(state: BreakdownState) -> Dict[str, Any]:
    """
    Generates detailed, actionable automotive diagnostics and roadside triage
    for drivers dealing with vehicle problems or stranded situations.
    """
    llm = get_llm()
    query = state["query"]
    history = state.get("messages", [])

    system_prompt = """You are "CypherPunks Emergency Vehicle & Roadside Assistance AI", an expert automotive engineer and roadside diagnostic specialist.

Your task is to answer vehicle, car, and in-cabin breakdown problems according to the user's intent:

1. IF THE USER ASKS A SMALL / SIMPLE DOUBT:
   (e.g., "What does this dashboard light mean?", "Can I top up coolant with water?", "Why is my AC blowing hot air?", "What is recommended tyre pressure?", "Is squeaking brake normal?"):
   - Deliver a BRIEF, CONCISE, AND DIRECT SOLUTION.
   - Do NOT output long essays or overwhelming blocks of text.
   - State the core cause directly and provide 2-3 quick actionable steps or rules of thumb.

2. IF THE USER IS STRANDED OR EXPERIENCING A MAJOR BREAKDOWN / EMERGENCY:
   (e.g., engine overheating, smoking, flat tyre on highway, car completely dead, brake failure):
   - Provide structured roadside triage:
     1. 🚨 Immediate Safety Action (hazard lights, parking safely)
     2. 🔍 Probable Diagnosis & Severity
     3. 🛠️ Step-by-Step Roadside Fix / Triage
     4. 🚦 Safe to Drive vs. Tow Recommendation
     5. 📞 2-Sentence Mechanic Summary

Keep all responses helpful, accurate, and easy to read on a mobile phone screen for a driver."""


    conversation = [SystemMessage(content=system_prompt)]
    
    # Add recent history if available
    for msg in history[-6:]:
        role = msg.get("role", "user")
        text = msg.get("content", "")
        if role == "user":
            conversation.append(HumanMessage(content=text))
        elif role == "assistant":
            conversation.append(AIMessage(content=text))

    conversation.append(HumanMessage(content=query))

    response = llm.invoke(conversation)
    return {
        "response": extract_text(response.content),
        "urgency": "IN_SCOPE_DIAGNOSED",
        "diagnosis": "Automotive diagnosis generated successfully."
    }



# Routing Condition
def route_guardrail(state: BreakdownState) -> str:
    if state["is_car_related"]:
        return "diagnostic_node"
    return "out_of_scope_node"


# Build the Graph
workflow = StateGraph(BreakdownState)

workflow.add_node("guardrail_node", guardrail_node)
workflow.add_node("out_of_scope_node", out_of_scope_node)
workflow.add_node("diagnostic_node", diagnostic_node)

workflow.set_entry_point("guardrail_node")

workflow.add_conditional_edges(
    "guardrail_node",
    route_guardrail,
    {
        "diagnostic_node": "diagnostic_node",
        "out_of_scope_node": "out_of_scope_node",
    }
)

workflow.add_edge("diagnostic_node", END)
workflow.add_edge("out_of_scope_node", END)

# Compile graph
breakdown_graph = workflow.compile()
