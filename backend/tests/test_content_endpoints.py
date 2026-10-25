from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_content_tree_endpoint():
    """Kiểm tra endpoint GET /api/v1/content/tree trả về danh mục cây phân cấp"""
    res = client.get("/api/v1/content/tree")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Tìm group_plans
    plans_group = next((item for item in data if item["id"] == "group_plans"), None)
    assert plans_group is not None
    assert plans_group["type"] == "folder"
    assert len(plans_group["children"]) > 0

def test_content_note_endpoint():
    """Kiểm tra endpoint GET /api/v1/content/note đọc và phân giải markdown"""
    res = client.get("/api/v1/content/note?path=plans/week-01/test-1-listening-p3-p4.md")
    assert res.status_code == 200
    note = res.json()
    assert "title" in note
    assert "raw_content" in note
    assert "exam_metadata" in note
    assert "headings" in note
    assert note["exam_metadata"]["start_q"] == 21
    assert note["exam_metadata"]["end_q"] == 40
    assert note["exam_metadata"]["has_exam"] is True

def test_static_audio_mount():
    """Kiểm tra FastAPI mount static /assets/audio/ phục vụ trực tiếp từ content/assets/audio"""
    # Gửi request tới 1 file mp3 có sẵn
    res = client.get("/assets/audio/cam18-test1-part1.mp3")
    assert res.status_code in (200, 206)
    assert "audio" in res.headers.get("content-type", "")
