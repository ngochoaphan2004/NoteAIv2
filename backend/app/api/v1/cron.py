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
    Kích hoạt thực thi Cronjob ngay lập tức (Dùng để test khả năng của Cronjob mà không cần đợi đến 23:59).
    Thực hiện 6 tác vụ tự trị trọn gói:
    1. Quét và đồng bộ toàn bộ từ vựng Markdown sang PostgreSQL (FSRS v4)
    2. Kiểm tra tính toàn vẹn của Knowledge Garden & Dead Links
    3. Thống kê số lượng thẻ cần ôn hôm nay
    4. Tự động đồng bộ kế hoạch theo ngày và tiến độ học tập
    5. Tự động đánh giá tuần cũ và chuẩn bị kế hoạch tuần mới vào Chủ Nhật
    6. TỰ ĐỘNG BIÊN DỊCH VÀ XUẤT BẢN TOÀN BỘ DỰ ÁN QUARTZ (`npm run quartz -- build`)
    """
    result = await cron_scheduler.execute_jobs()
    return {
        "message": "Cronjob đã được kích hoạt và thực thi thành công!",
        "result": result
    }

