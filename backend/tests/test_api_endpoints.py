from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["ports"]["backend"] == 8000
    assert data["ports"]["database_pg"] == 5433
    assert data["ports"]["qdrant"] == 6333

def test_flashcard_stats_endpoint():
    response = client.get("/api/v1/flashcards/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_cards" in data
    assert "retention_rate" in data
    assert data["total_cards"] >= 60

def test_flashcards_due_endpoint():
    response = client.get("/api/v1/flashcards/due?limit=5")
    assert response.status_code == 200
    cards = response.json()
    assert isinstance(cards, list)
    if cards:
        first_card = cards[0]
        assert "front" in first_card
        assert "preview_intervals" in first_card
        assert "good" in first_card["preview_intervals"]

def test_agent_evaluate_endpoint():
    payload = {
        "attempt_text": "3 dentist\n12 a\n1 dw137yz - dw307yz / lý do: nghe nhầm",
        "skill": "listening"
    }
    response = client.post("/api/v1/agents/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) == 3
