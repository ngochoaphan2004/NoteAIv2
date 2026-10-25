from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["ports"]["gateway_unified"] == 8000
    assert data["ports"]["database_pg"] in (5432, 5433)
    assert data["ports"]["qdrant"] == 6333

def test_flashcard_stats_endpoint():
    response = client.get("/api/v1/flashcards/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_cards" in data
    assert "retention_rate" in data
    assert data["total_cards"] >= 0

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
    assert "ICT" in data["schedule"]

def test_auth_login_and_verify_flow():
    # 1. Thử login sai mật khẩu -> 401
    bad_res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert bad_res.status_code == 401

    # 2. Thử login đúng mật khẩu -> 200
    good_res = client.post("/api/v1/auth/login", json={"username": settings.AUTH_USERNAME, "password": settings.AUTH_PASSWORD})
    assert good_res.status_code == 200
    data = good_res.json()
    assert data["status"] == "success"
    assert "access_token" in data
    token = data["access_token"]

    # 3. Thử verify với token -> 200
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["authenticated"] is True
    assert me_res.json()["user"]["username"] == "admin"

    # 4. Thử verify không có token -> 401
    no_token_res = client.get("/api/v1/auth/me")
    assert no_token_res.status_code == 401

def test_spa_and_static_serving():
    # 1. Trình duyệt truy cập root (mặc định) -> trả về SPA HTML
    res = client.get("/")
    assert res.status_code == 200
    assert "<!doctype html>" in res.text.lower()

    # 2. Truy cập với query format=json -> trả về JSON health check
    json_res = client.get("/?format=json")
    assert json_res.status_code == 200
    assert json_res.json()["status"] == "online"

    # 3. Trình duyệt truy cập một route SPA bất kỳ (ví dụ: /plans) -> trả về SPA HTML
    spa_res = client.get("/plans", headers={"accept": "text/html"})
    assert spa_res.status_code == 200
    assert "<!doctype html>" in spa_res.text.lower()

    # 4. Yêu cầu file tĩnh favicon.ico -> trả về 200
    fav_res = client.get("/favicon.ico")
    assert fav_res.status_code == 200


