import os
import logging
import tempfile
import pytest
from app.core.logging_config import setup_logging

def test_setup_logging_creates_files():
    """Kiểm tra setup_logging tạo đúng các file app.log và error.log"""
    temp_dir = tempfile.mkdtemp()
    os.environ["LOG_DIR"] = temp_dir
    try:
        log_dir = setup_logging()
        assert os.path.exists(log_dir)

        logger = logging.getLogger("test_logger")
        logger.info("Thử nghiệm ghi log info vào hệ thống")
        logger.warning("Thử nghiệm ghi log warning vào hệ thống")
        logger.error("Thử nghiệm ghi log error vào hệ thống")

        app_log = os.path.join(temp_dir, "app.log")
        error_log = os.path.join(temp_dir, "error.log")

        assert os.path.exists(app_log)
        assert os.path.exists(error_log)

        # Đóng toàn bộ handlers để giải phóng file lock trên Windows
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            handler.flush()
            handler.close()
            root_logger.removeHandler(handler)

        with open(app_log, "r", encoding="utf-8") as f:
            app_content = f.read()
            assert "Thử nghiệm ghi log info" in app_content
            assert "Thử nghiệm ghi log warning" in app_content
            assert "Thử nghiệm ghi log error" in app_content

        with open(error_log, "r", encoding="utf-8") as f:
            error_content = f.read()
            # Log INFO tuyệt đối không xuất hiện trong error.log
            assert "Thử nghiệm ghi log info" not in error_content
            # Warning và Error bắt buộc phải có
            assert "Thử nghiệm ghi log warning" in error_content
            assert "Thử nghiệm ghi log error" in error_content
    finally:
        if "LOG_DIR" in os.environ:
            del os.environ["LOG_DIR"]
        # Phục hồi logging về bình thường
        setup_logging()
        # Dọn dẹp thư mục tạm an toàn
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_system_logs_api_endpoint():
    """Kiểm tra router đọc log hệ thống qua FastAPI TestClient"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Test endpoint xem logs
    res = client.get("/api/v1/system/logs?log_type=app&lines=50")
    assert res.status_code == 200
    data = res.json()
    assert "lines" in data
    assert "total_lines_returned" in data

    # 2. Test endpoint xem health metrics
    res_health = client.get("/api/v1/system/health-metrics")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "healthy"
    assert "disk" in data_health
    assert "free_gb" in data_health["disk"]

