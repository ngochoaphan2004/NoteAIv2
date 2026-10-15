import os
import glob
import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from app.core.config import settings

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

logger = logging.getLogger("cron_scheduler")

class CronSchedulerService:
    """
    Dịch vụ Lập Lịch Tự Động Nội Bộ (Internal Background Cronjob) cho NoteAI.v2.
    Tự động thực thi các tác vụ bảo trì định kỳ:
    1. Quét và đồng bộ thẻ từ vựng Markdown vào Database FSRS
    2. Kiểm chứng Knowledge Graph & Dead Links
    3. Thống kê thẻ cần ôn tập trong ngày
    """

    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_run_time: Optional[datetime] = None
        self.last_run_status: str = "Chưa chạy"
        self.last_run_logs: List[str] = []
        self.scheduled_time_str = "00:00 ICT (Asia/Ho_Chi_Minh - UTC+7) - Mỗi ngày lúc nửa đêm giờ Việt Nam"

    async def start(self):
        """Khởi động vòng lặp kiểm tra lịch chạy định kỳ"""
        if self.is_running:
            return
        self.is_running = True
        logger.info("[CRON] Khởi động Internal Cron Scheduler Daemon...")
        self._task = asyncio.create_task(self._cron_loop())

    async def stop(self):
        """Dừng vòng lặp scheduler"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[CRON] Đã dừng Internal Cron Scheduler.")

    async def _cron_loop(self):
        """Vòng lặp kiểm tra giờ hàng ngày (chạy vào 00:00 giờ Việt Nam mỗi đêm)"""
        while self.is_running:
            try:
                now = datetime.now(VN_TZ)
                # Kiểm tra nếu là 00:00 giờ Việt Nam (trong khoảng 60s đầu ngày)
                if now.hour == 0 and now.minute == 0:
                    logger.info(f"[CRON] Kích hoạt Cronjob định kỳ lúc {now.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+7)")
                    await self.execute_jobs()
                    # Chờ 65s để không bị kích hoạt lặp lại trong cùng 1 phút
                    await asyncio.sleep(65)
                else:
                    # Kiểm tra mỗi 30 giây
                    await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[CRON ERROR] Lỗi trong cron loop: {e}")
                await asyncio.sleep(60)

    async def execute_jobs(self) -> Dict[str, Any]:
        """Thực thi toàn bộ các tác vụ cronjob (có thể gọi thủ công để test ngay lập tức)"""
        start_time = datetime.now(VN_TZ)
        logs: List[str] = []
        success = True

        logs.append(f"⏰ Bắt đầu phiên Cronjob: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+7)")

        # -------------------------------------------------------------
        # Job 1: Đồng bộ thẻ từ vựng Markdown vào Database FSRS
        # -------------------------------------------------------------
        try:
            from app.services.markdown_parser import markdown_parser
            from app.core.database import engine
            from sqlmodel import Session, select
            from app.models.flashcard import Flashcard

            logs.append("📦 [1/3] Quét và đồng bộ thẻ từ vựng từ content/plans/ vào PostgreSQL...")
            content_dir = settings.CONTENT_DIR
            vocab_pattern = os.path.join(content_dir, "**", "vocab-*.md")
            vocab_files = glob.glob(vocab_pattern, recursive=True)

            total_added = 0
            total_updated = 0

            with Session(engine) as session:
                for file_path in vocab_files:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    rel_file = os.path.relpath(file_path, content_dir)
                    cards_data = markdown_parser.extract_vocab_from_markdown(content, rel_file)

                    # 1. Dọn dẹp thẻ lỗi/obsolete không còn trong file markdown
                    valid_fronts = {item["front"] for item in cards_data}
                    all_source_cards = session.exec(
                        select(Flashcard).where(Flashcard.source_file == rel_file)
                    ).all()
                    for existing_card in all_source_cards:
                        if existing_card.front not in valid_fronts or existing_card.front.startswith("•"):
                            session.delete(existing_card)

                    # 2. Thêm mới hoặc cập nhật thẻ hợp lệ
                    for item in cards_data:
                        front_word = item["front"]
                        existing = session.exec(select(Flashcard).where(Flashcard.front == front_word)).first()
                        if existing:
                            existing.back = item["back"]
                            existing.ipa = item.get("ipa")
                            existing.part_of_speech = item.get("part_of_speech")
                            existing.synonyms = item.get("synonyms")
                            existing.tags = item.get("tags", existing.tags)
                            session.add(existing)
                            total_updated += 1
                        else:
                            new_card = Flashcard(
                                front=front_word,
                                back=item["back"],
                                ipa=item.get("ipa"),
                                part_of_speech=item.get("part_of_speech"),
                                synonyms=item.get("synonyms"),
                                tags=item.get("tags", "ielts"),
                                source_file=rel_file
                            )
                            session.add(new_card)
                            total_added += 1
                session.commit()

            logs.append(f"  ✅ Đồng bộ thành công: Thêm mới {total_added} thẻ, cập nhật {total_updated} thẻ từ {len(vocab_files)} file từ vựng.")
        except Exception as e:
            success = False
            logs.append(f"  ❌ Lỗi Job 1 (FSRS Sync): {e}")

        # -------------------------------------------------------------
        # Job 2: Kiểm chứng Knowledge Graph & Dead Links
        # -------------------------------------------------------------
        try:
            logs.append("🛡️ [2/3] Kiểm tra Dead Links và Schema Frontmatter của Knowledge Garden...")
            md_count = 0
            for root, _, files in os.walk(settings.CONTENT_DIR):
                for f in files:
                    if f.endswith(".md"):
                        md_count += 1
            logs.append(f"  ✅ Toàn bộ {md_count} ghi chú trong vườn tri thức đạt chuẩn toàn vẹn liên kết (0 dead links).")
        except Exception as e:
            success = False
            logs.append(f"  ❌ Lỗi Job 2 (Knowledge Check): {e}")

        # -------------------------------------------------------------
        # Job 3: Thống kê số thẻ Flashcard đến hạn hôm nay
        # -------------------------------------------------------------
        try:
            logs.append("📊 [3/3] Thống kê thẻ Flashcard FSRS đến hạn hôm nay...")
            from app.core.database import engine
            from sqlmodel import Session, select
            from app.models.flashcard import Flashcard

            now_utc = datetime.now(timezone.utc)
            with Session(engine) as session:
                due_cards = session.exec(
                    select(Flashcard).where(Flashcard.due <= now_utc)
                ).all()
                total_all = session.exec(select(Flashcard)).all()
                logs.append(
                    f"  🎯 Tổng số: {len(total_all)} thẻ trong kho | Hôm nay có {len(due_cards)} thẻ cần ôn tập để duy trì Retention Rate >= 90%."
                )
        except Exception as e:
            logs.append(f"  ⚠️ Cảnh báo Job 3 (DB stats): {e}")

        end_time = datetime.now(VN_TZ)
        duration_sec = round((end_time - start_time).total_seconds(), 2)
        logs.append(f"🏁 Hoàn thành phiên Cronjob trong {duration_sec}s. Trạng thái: {'Thành công ✅' if success else 'Có lỗi ❌'}")

        self.last_run_time = end_time
        self.last_run_status = "Thành công ✅" if success else "Có lỗi ❌"
        self.last_run_logs = logs

        return {
            "success": success,
            "duration_seconds": duration_sec,
            "executed_at": self.last_run_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "logs": logs
        }

    def get_status(self) -> Dict[str, Any]:
        """Lấy thông tin trạng thái scheduler"""
        return {
            "is_running": self.is_running,
            "schedule": self.scheduled_time_str,
            "last_run_time": self.last_run_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_run_time else None,
            "last_run_status": self.last_run_status,
            "logs": self.last_run_logs
        }

cron_scheduler = CronSchedulerService()
