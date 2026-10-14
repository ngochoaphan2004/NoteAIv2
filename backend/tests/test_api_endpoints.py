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

def test_system_config_endpoints():
    # 1. GET /api/v1/system/config
    response = client.get("/api/v1/system/config")
    assert response.status_code == 200
    data = response.json()
    assert "llm_provider" in data
    assert "llm_model" in data
    assert "llm_models" in data
    assert "cron_timezone" in data
    assert data["cron_timezone"] == "Asia/Ho_Chi_Minh"
    assert data["ports"]["database_postgres"] == 5433

    # 2. POST /api/v1/system/config update in-memory
    update_payload = {
        "llm_model": "gemini-1.5-flash",
        "watchdog_enabled": True
    }
    post_res = client.post("/api/v1/system/config", json=update_payload)
    assert post_res.status_code == 200
    assert post_res.json()["success"] is True

def test_cron_status_endpoint():
    response = client.get("/api/v1/cron/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert "schedule" in data
    assert "Asia/Ho_Chi_Minh" in data["schedule"]

