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
        from app.services.plan_service import plan_service

        res = plan_service.sync_all_plans()
        return res
    except Exception as e:
        logger.error(f"Lỗi khi kích hoạt đồng bộ kế hoạch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-next-week")
def generate_next_week(
    target_week_number: int = 2,
    force: bool = False
) -> Dict[str, Any]:
    """
    Kích hoạt Weekly Cronjob / Planning Agent:
    1. Đánh giá tuần cũ từ PostgreSQL (Test attempts, trap types, flashcards).
    2. Gọi LLM viết bản nhận xét tổng kết tuần (Weekly Retrospective) và lưu vào file tuần cũ.
    3. Tự động sinh kế hoạch tuần mới (week-XX/index.md) với micro-sessions thích ứng.
    4. Tự động sinh các file bài làm chi tiết cho từng ngày (Listening, Reading, Writing, Vocab)
       tích hợp hình ảnh đề thi và audioscripts từ sách gốc Cambridge 18.
    5. Cập nhật liên kết cấp macro và rebuild Quartz HTML.
    """
    try:
        from app.services.plan_generator import autonomous_plan_generator
        return autonomous_plan_generator.generate_next_week(
            target_week_number=target_week_number,
            force=force
        )
    except Exception as e:
        logger.error(f"Lỗi khi tự động tạo kế hoạch tuần {target_week_number}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrospective/{week_number}")
def get_weekly_retrospective(week_number: int) -> Dict[str, Any]:
    """Xem trước bản đánh giá và phân tích lỗi sai tuần cũ từ AI"""
    try:
        from app.services.plan_generator import autonomous_plan_generator
        return autonomous_plan_generator.evaluate_past_week(week_number)
    except Exception as e:
        logger.error(f"Lỗi khi tạo retrospective cho tuần {week_number}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


