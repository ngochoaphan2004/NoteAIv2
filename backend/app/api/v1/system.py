import os
import shutil
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from app.core.logging_config import get_log_dir

router = APIRouter(prefix="/system", tags=["System Monitoring & Logs"])

@router.get("/logs")
def get_recent_logs(
    log_type: str = Query(default="app", pattern="^(app|error)$", description="Loại log: 'app' hoặc 'error'"),
    lines: int = Query(default=100, ge=1, le=1000, description="Số dòng log cuối cùng cần đọc")
) -> Dict[str, Any]:
    """
    Đọc n dòng log gần nhất trực tiếp từ server để theo dõi từ xa qua Web/API.
    Tránh tình trạng mất log hoặc phải SSH vào VPS để đọc log.
    """
    log_dir = get_log_dir()
    file_name = "error.log" if log_type == "error" else "app.log"
    file_path = os.path.join(log_dir, file_name)

    if not os.path.exists(file_path):
        return {
            "log_type": log_type,
            "file": file_path,
            "total_lines": 0,
            "lines": [f"Chưa có dữ liệu ghi log trong file {file_name}."]
        }

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            # Bỏ ký tự xuống dòng ở cuối
            cleaned_lines = [line.rstrip("\r\n") for line in recent_lines]

        return {
            "log_type": log_type,
            "file": file_name,
            "total_lines_returned": len(cleaned_lines),
            "lines": cleaned_lines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể đọc file log: {e}")

@router.get("/log-files")
def list_log_files() -> List[Dict[str, Any]]:
    """Liệt kê danh sách tất cả các file log hiện có trong thư mục logs/ và kích thước của chúng"""
    log_dir = get_log_dir()
    result: List[Dict[str, Any]] = []

    if os.path.exists(log_dir):
        for root, _, files in os.walk(log_dir):
            for file in sorted(files):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, log_dir)
                size_bytes = os.path.getsize(full_path)
                result.append({
                    "name": rel_path.replace("\\", "/"),
                    "size_bytes": size_bytes,
                    "size_human": f"{round(size_bytes / 1024, 1)} KB" if size_bytes < 1024*1024 else f"{round(size_bytes / (1024*1024), 2)} MB",
                    "modified_at": os.path.getmtime(full_path)
                })

    return result

@router.get("/logs/download")
def download_log_file(file_name: str = Query(..., description="Tên file log cần tải, ví dụ: 'app.log' hoặc 'error.log'")):
    """Tải xuống file log hoàn chỉnh về máy để phân tích ngoại tuyến"""
    log_dir = get_log_dir()
    # Ngăn Directory Traversal
    safe_name = os.path.basename(file_name)
    file_path = os.path.join(log_dir, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File log không tồn tại.")

    return FileResponse(file_path, filename=safe_name, media_type="text/plain")

@router.get("/health-metrics")
def get_system_health():
    """Kiểm tra sức khỏe hệ thống: dung lượng ổ cứng, RAM và trạng thái ghi log"""
    log_dir = get_log_dir()
    total, used, free = shutil.disk_usage(log_dir)

    return {
        "status": "healthy",
        "log_directory": log_dir,
        "disk": {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "free_percentage": f"{round((free / total) * 100, 1)}%"
        }
    }


# -------------------------------------------------------------
# Configuration Management & LLM Connectivity
# -------------------------------------------------------------
from pydantic import BaseModel
import time
from app.core.config import settings

class UpdateConfigRequest(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_models: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    watchdog_enabled: Optional[bool] = None

class TestLLMRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None

def _mask_key(key: Optional[str]) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"

def _save_env_file(updates: Dict[str, str]):
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}\n")
                updated_keys.add(k)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

@router.get("/config")
def get_system_config():
    """Lấy danh sách các thông số cấu hình hệ thống hiện tại"""
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_models": settings.LLM_MODELS or "gemini-1.5-flash,gemini-2.0-flash,gemini-1.5-flash-8b,gemini-1.5-pro",
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "gemini_api_key_masked": _mask_key(settings.GEMINI_API_KEY),
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "openai_api_key_masked": _mask_key(settings.OPENAI_API_KEY),
        "database_url": settings.DATABASE_URL,
        "qdrant_url": settings.QDRANT_URL,
        "qdrant_collection": settings.QDRANT_COLLECTION,
        "content_dir": settings.CONTENT_DIR,
        "environment": settings.ENVIRONMENT,
        "watchdog_enabled": settings.WATCHDOG_ENABLED,
        "cron_timezone": "Asia/Ho_Chi_Minh",
        "cron_schedule": "00:00 ICT (Chuyển giao ngày mới) & 23:59 ICT (Tổng kết & FSRS Sync)",
        "ports": {
            "database_postgres": 5432 if ":5432" in settings.DATABASE_URL else 5433,
            "qdrant_rest": 6333,
            "qdrant_grpc": 6334,
            "fastapi_backend": settings.PORT,
            "quartz_preview": 8088,
            "frontend_spa": settings.PORT
        }
    }

@router.post("/config")
def update_system_config(req: UpdateConfigRequest):
    """
    Cập nhật các thông số cấu hình hệ thống trực tiếp vào runtime và lưu trữ bền vững vào .env
    """
    env_updates: Dict[str, str] = {}

    if req.llm_provider is not None:
        settings.LLM_PROVIDER = req.llm_provider.strip().lower()
        env_updates["LLM_PROVIDER"] = settings.LLM_PROVIDER

    if req.llm_model is not None and req.llm_model.strip():
        settings.LLM_MODEL = req.llm_model.strip()
        env_updates["LLM_MODEL"] = settings.LLM_MODEL

    if req.llm_models is not None and req.llm_models.strip():
        settings.LLM_MODELS = req.llm_models.strip()
        env_updates["LLM_MODELS"] = settings.LLM_MODELS

    if req.gemini_api_key is not None and req.gemini_api_key.strip():
        settings.GEMINI_API_KEY = req.gemini_api_key.strip()
        env_updates["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

    if req.openai_api_key is not None and req.openai_api_key.strip():
        settings.OPENAI_API_KEY = req.openai_api_key.strip()
        env_updates["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

    if req.watchdog_enabled is not None:
        settings.WATCHDOG_ENABLED = req.watchdog_enabled
        env_updates["WATCHDOG_ENABLED"] = "true" if req.watchdog_enabled else "false"

    if env_updates:
        try:
            _save_env_file(env_updates)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Không thể ghi file .env: {e}")

    return {
        "success": True,
        "message": "Đã cập nhật và lưu cấu hình hệ thống thành công!",
        "updated_keys": list(env_updates.keys())
    }

@router.post("/test-llm")
def test_llm_connection(req: Optional[TestLLMRequest] = None):
    """
    Thử nghiệm kết nối tới Cloud LLM với danh sách mô hình dự phòng (Fallback Manager),
    đo độ trễ (latency ms) và phản hồi thực tế từ API.
    """
    import time
    start_time = time.time()
    test_prompt = "Hãy phản hồi ngắn gọn đúng 1 từ: 'CONNECTED'"

    try:
        from app.services.llm_service import llm_service

        response_text = llm_service.generate_text(
            prompt=test_prompt,
            system_message="Bạn là trợ lý kiểm tra kết nối hệ thống. Trả lời đúng 1 từ."
        )
        latency_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "success": True,
            "model_used": llm_service.last_used_model or settings.LLM_MODEL,
            "latency_ms": latency_ms,
            "provider": settings.LLM_PROVIDER,
            "response": response_text.strip(),
            "message": f"Kết nối LLM thành công ({latency_ms}ms) qua mô hình {llm_service.last_used_model}!"
        }
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 1)
        err_msg = str(e)
        return {
            "success": False,
            "error": err_msg,
            "latency_ms": latency_ms,
            "provider": settings.LLM_PROVIDER,
            "message": f"Kết nối thất bại ({latency_ms}ms): {err_msg}"
        }

