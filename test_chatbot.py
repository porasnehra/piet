import sys
import os

# Ensure e:/Piet is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


from app.graph import breakdown_graph


def run_tests():
    print("=================================================================")
    print("Testing CypherPunks In-Vehicle Diagnostics & Guardrail Chatbot")
    print("=================================================================\n")

    test_cases = [
        {
            "query": "My engine is overheating with steam coming from under the bonnet while stuck on a highway.",
            "expected_car": True,
            "label": "Car Problem: Engine Overheating on Highway"
        },
        {
            "query": "When I turn the key in the ignition, I hear rapid clicking sounds and the car will not start.",
            "expected_car": True,
            "label": "Car Problem: Dead Battery / Starter Clicking"
        },
        {
            "query": "Can you write a python script to sort an array using quicksort?",
            "expected_car": False,
            "label": "Off-topic Query: Python Programming"
        },
        {
            "query": "What is the best recipe for baking chocolate chip cookies?",
            "expected_car": False,
            "label": "Off-topic Query: Baking Recipe"
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"--- Test #{i}: {test['label']} ---")
        print(f"Query: \"{test['query']}\"")
        
        inputs = {
            "messages": [],
            "query": test["query"],
            "is_car_related": False,
            "urgency": "PENDING",
            "diagnosis": "",
            "response": ""
        }

        try:
            result = breakdown_graph.invoke(inputs)
            is_car = result.get("is_car_related", False)
            response = result.get("response", "")

            print(f"Detected is_car_related: {is_car}")
            print(f"Urgency Status: {result.get('urgency')}")
            print(f"Preview Response:\n{response[:200]}...\n")

            if is_car == test["expected_car"]:
                print(f"-> Result: PASS (Match expected guardrail classification: {test['expected_car']})\n")
            else:
                print(f"-> Result: FAIL (Expected is_car_related={test['expected_car']}, got {is_car})\n")
                all_passed = False

        except Exception as e:
            print(f"-> Error executing test: {e}\n")
            all_passed = False

    print("=================================================================")
    if all_passed:
        print("ALL TESTS PASSED! Strict guardrails & car diagnostics working.")
    else:
        print("Some tests failed. Please inspect logs.")
    print("=================================================================")


if __name__ == "__main__":
    run_tests()
