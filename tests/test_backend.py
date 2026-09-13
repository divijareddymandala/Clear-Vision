import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

def run_tests():
    print("[1/6] Initializing test database...")
    init_db()

    client = TestClient(app)

    print("[2/6] Testing GET /api/health...")
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    assert health_data["status"] == "online"
    print(" -> Health OK:", health_data["service"], "| Total Reviews:", health_data["total_reviews"])

    print("[3/6] Testing GET /api/reviews...")
    resp = client.get("/api/reviews")
    assert resp.status_code == 200
    reviews = resp.json()
    assert len(reviews) >= 6, "Expected at least 6 seeded reviews"
    print(f" -> Found {len(reviews)} reviews in database")

    print("[4/6] Testing POST /api/reviews (LLM/NLP sentiment analysis & response drafting)...")
    new_review_payload = {
        "name": "Alexander Hayes",
        "platform": "Google",
        "rating": 1,
        "category": "Room Quality",
        "text": "Worst hotel experience ever. The shower had no hot water, and the air conditioner made a deafening rattling sound all night. Front desk staff hung up on me when I called for maintenance.",
        "auto_analyze": True
    }
    resp = client.post("/api/reviews", json=new_review_payload)
    assert resp.status_code == 200, f"Create review failed: {resp.text}"
    created = resp.json()
    assert created["sentiment"] == "negative", f"Expected negative sentiment, got {created['sentiment']}"
    assert created["score"] < 40, f"Expected low sentiment score, got {created['score']}"
    assert len(created["issues"]) > 0, "Expected extracted issues"
    assert created["response"] is not None and len(created["response"]) > 50
    assert created["churn_risk_score"] > 60
    print(" -> Successfully analyzed review! Sentiment:", created["sentiment"], "Score:", created["score"], "Issues:", created["issues"])
    print(" -> AI Response Drafted:", created["response"][:80] + "...")

    print("[5/6] Testing POST /api/analyze (Direct sentiment analysis)...")
    analyze_payload = {
        "text": "Remarkable service! The breakfast buffet was fresh and delightful, and Priya at reception was wonderful.",
        "rating": 5,
        "guest_name": "Sophia L."
    }
    resp = client.post("/api/analyze", json=analyze_payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["analysis"]["sentiment"] == "positive"
    assert res_data["analysis"]["score"] >= 80
    print(" -> Direct Analysis OK: Positive score =", res_data["analysis"]["score"])

    print("[6/6] Testing GET /api/stats, /api/churn-alerts, /api/staff, /api/competitors...")
    stats = client.get("/api/stats").json()
    assert "overall_rating" in stats
    assert stats["total_reviews"] >= 7

    churn = client.get("/api/churn-alerts").json()
    assert len(churn) >= 1

    staff = client.get("/api/staff").json()
    assert len(staff) >= 4

    comp = client.get("/api/competitors").json()
    assert len(comp["rankings"]) >= 5

    print("\n[SUCCESS] ALL BACKEND UNIT & INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
