from fastapi import APIRouter
from app.core.scheduler import cron_scheduler

router = APIRouter(prefix="/cron", tags=["Periodic Cronjobs"])

@router.get("/status")
def get_cronjob_status():
    """Kiểm tra cấu hình, lịch trình và nhật ký lần chạy gần nhất của Cronjob"""
    return cron_scheduler.get_status()

@router.post("/trigger")
async def trigger_cronjob_now():
    """
    Kích hoạt thực thi Cronjob ngay lập tức (Dùng để test khả năng của Cronjob mà không cần đợi đến 00:00).
    Thực hiện:
    1. Quét và đồng bộ toàn bộ từ vựng Markdown sang FSRS
    2. Kiểm tra tính toàn vẹn của Knowledge Garden & Dead Links
    3. Thống kê số lượng thẻ cần ôn hôm nay
    """
    result = await cron_scheduler.execute_jobs()
    return {
        "message": "Cronjob đã được kích hoạt và thực thi thành công!",
        "result": result
    }
