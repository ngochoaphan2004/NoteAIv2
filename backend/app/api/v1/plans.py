import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.services.plan_service import plan_service

router = APIRouter(prefix="/plans", tags=["Study Plans & Daily Pacing"])
logger = logging.getLogger("plans_api")

@router.get("/today")
def get_today_mission() -> Dict[str, Any]:
    """
    Lấy thông tin nhiệm vụ học tập của ngày hôm nay (tự động nhận diện theo ngày tháng hiện tại).
    Bao gồm: Kỹ năng trọng tâm, thời lượng micro-session (30-35p), link bài làm, trạng thái hoàn thành.
    """
    try:
        return plan_service.get_today_task_summary()
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin nhiệm vụ hôm nay: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
def trigger_plan_sync() -> Dict[str, Any]:
    """
    Kích hoạt AI tự động đồng bộ toàn bộ các file Markdown kế hoạch theo ngày tháng thực tế
    và tình trạng hoàn thành bài thi từ CSDL PostgreSQL.
    """
    try:
        from app.services.plan_service import plan_service, rebuild_quartz
        import threading

        res = plan_service.sync_all_plans()
        if res.get("updated_files"):
            threading.Thread(target=rebuild_quartz, daemon=True).start()
            res["quartz_rebuilding"] = True
        return res
    except Exception as e:
        logger.error(f"Lỗi khi kích hoạt đồng bộ kế hoạch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

