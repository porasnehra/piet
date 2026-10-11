import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api():
    print("=== Testing 1: Unauthorized Request (Missing / Wrong Key) ===")
    res_bad = client.post("/api/chat", json={"message": "car won't start"}, headers={"X-API-Key": "wrong-key"})
    print("Status:", res_bad.status_code, "->", res_bad.json())
    assert res_bad.status_code == 401, "Should reject wrong API key"

    print("\n=== Testing 2: Small Car Doubt (Brief Solution Expected) ===")
    res_brief = client.post(
        "/api/chat", 
        json={"message": "Can I add normal water into the engine coolant reservoir?"},
        headers={"X-API-Key": "cypherpunks-secret-key-2024"}
    )
    print("Status:", res_brief.status_code)
    data = res_brief.json()
    print("Car related:", data["is_car_related"])
    print("Brief Response:\n", data["response"])

    print("\n=== Testing 3: Wrong / Off-Topic Question (Guardrail Stoppage) ===")
    res_offtopic = client.post(
        "/api/chat", 
        json={"message": "Who is the CEO of Google?"},
        headers={"X-API-Key": "cypherpunks-secret-key-2024"}
    )
    data_off = res_offtopic.json()
    print("Car related:", data_off["is_car_related"])
    print("Guardrail Response:\n", data_off["response"])
    assert data_off["is_car_related"] == False, "Must block off-topic question"

    print("\n ALL VERIFICATIONS SUCCESSFUL!")

if __name__ == "__main__":
    test_api()
