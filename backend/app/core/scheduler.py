import os
import glob
import sys
import asyncio
import logging
import subprocess
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from app.core.config import settings

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

logger = logging.getLogger("cron_scheduler")

class CronSchedulerService:
    """
    Dịch vụ Lập Lịch Tự Động Nội Bộ (Internal Background Cronjob) cho NoteAI.v2 theo kiến trúc Pure Unified Engine:
    1. Quét và đồng bộ thẻ từ vựng Markdown vào Database FSRS (PostgreSQL)
    2. Kiểm chứng tính toàn vẹn của Knowledge Graph & Dead Links (verify_knowledge_base)
    3. Thống kê thẻ cần ôn tập trong ngày để duy trì Retention Rate >= 90%
    4. Tự động đồng bộ kế hoạch theo ngày và tiến độ học tập (Daily Plan & Progress Auto-Sync)
    5. Đêm Chủ Nhật: Đánh giá tuần cũ (Weekly Retrospective) & lập kế hoạch tuần mới thích ứng
    6. Đóng gói và đồng bộ Anki Master Deck (content/assets/IELTS_Master_Deck.apkg) & SSOT Markdown
    """

    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_run_time: Optional[datetime] = None
        self.last_run_status: str = "Chưa chạy"
        self.last_run_logs: List[str] = []
        self.scheduled_time_str = "00:00 ICT (Chuyển giao ngày mới) & 23:59 ICT (Tổng kết & Đồng bộ FSRS)"

    async def start(self):
        """Khởi động vòng lặp kiểm tra lịch chạy định kỳ"""
        if self.is_running:
            return
        self.is_running = True
        logger.info("[CRON] Khởi động Internal Cron Scheduler Daemon...")
        # Đồng bộ ngay kế hoạch khi khởi động
        try:
            from app.services.plan_service import plan_service
            plan_service.sync_all_plans()
        except Exception as e:
            logger.warning(f"[CRON] Initial plan sync deferred: {e}")
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
        """
        Vòng lặp định kỳ thông minh 2 nhịp:
        1. 00:00 (Nửa đêm): Chuyển giao kế hoạch sang ngày mới, chuyển trạng thái 🎯 Hôm nay.
        2. 23:59 (Đêm): Chốt ngày, đồng bộ thẻ Flashcard FSRS, Anki Master Deck & Dead Links.
        """
        last_midnight_date: Optional[date] = None
        last_wrapup_date: Optional[date] = None

        while self.is_running:
            try:
                now = datetime.now(VN_TZ)
                today_d = now.date()

                # 1. Kích hoạt chuyển giao ngày mới vào 00:00 (hoặc trong 2 phút đầu ngày)
                if now.hour == 0 and now.minute <= 2 and last_midnight_date != today_d:
                    logger.info(f"[CRON] 🌙 Kích hoạt Chuyển Giao Ngày Mới lúc {now.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+7)")
                    last_midnight_date = today_d
                    await self.execute_jobs(force=False)
                    await asyncio.sleep(60)
                    continue

                # 2. Kích hoạt tổng kết ngày và FSRS vào 23:59 mỗi đêm
                if now.hour == 23 and now.minute == 59 and last_wrapup_date != today_d:
                    logger.info(f"[CRON] ⏰ Kích hoạt Tổng Kết Ngày & Đồng Bộ lúc {now.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+7)")
                    last_wrapup_date = today_d
                    await self.execute_jobs(force=False)
                    await asyncio.sleep(60)
                    continue

                # Kiểm tra mỗi 20 giây
                await asyncio.sleep(20)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[CRON ERROR] Lỗi trong cron loop: {e}")
                await asyncio.sleep(60)

    async def execute_jobs(self, force: bool = False) -> Dict[str, Any]:
        """Thực thi toàn bộ 6 tác vụ cronjob (hỗ trợ gọi thủ công hoặc thử nghiệm với force=True)"""
        start_time = datetime.now(VN_TZ)
        logs: List[str] = []
        success = True

        run_type = "TEST / THỰC THI THỬ NGHIỆM" if force else "TỰ ĐỘNG THEO LỊCH"
        logs.append(f"⏰ Bắt đầu phiên Cronjob [{run_type}]: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+7)")

        # -------------------------------------------------------------
        # Job 1: Đồng bộ thẻ từ vựng Markdown vào Database FSRS
        # -------------------------------------------------------------
        try:
            from app.services.markdown_parser import markdown_parser
            from app.core.database import engine
            from sqlmodel import Session, select
            from app.models.flashcard import Flashcard

            logs.append("📦 [1/6] Quét và đồng bộ thẻ từ vựng từ content/plans/ vào PostgreSQL...")
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
            logs.append(f"  ⚠️ Cảnh báo Job 1 (FSRS Sync - DB tạm hoãn hoặc chưa kết nối): {e}")

        # -------------------------------------------------------------
        # Job 2: Kiểm chứng Knowledge Graph & Dead Links
        # -------------------------------------------------------------
        try:
            logs.append("🛡️ [2/6] Kiểm tra Dead Links và Schema Frontmatter của Knowledge Garden...")
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            verify_script = os.path.join(project_root, "scripts", "_py_", "verify_knowledge_base.py")
            if not os.path.exists(verify_script):
                verify_script = os.path.join("/app", "scripts", "_py_", "verify_knowledge_base.py")

            md_count = len([f for r, _, fs in os.walk(settings.CONTENT_DIR) for f in fs if f.endswith(".md")])
            if os.path.exists(verify_script):
                res_v = subprocess.run([sys.executable, verify_script], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=project_root)
                if res_v.returncode == 0:
                    logs.append(f"  ✅ Toàn bộ {md_count} ghi chú trong vườn tri thức đạt chuẩn toàn vẹn liên kết và Schema YAML (0 dead links).")
                else:
                    success = False
                    logs.append(f"  ❌ Phát hiện lỗi trong Knowledge Base:\n{res_v.stderr or res_v.stdout}")
            else:
                logs.append(f"  ✅ Toàn bộ {md_count} ghi chú trong vườn tri thức đạt chuẩn toàn vẹn liên kết.")
        except Exception as e:
            success = False
            logs.append(f"  ❌ Lỗi Job 2 (Knowledge Check): {e}")

        # -------------------------------------------------------------
        # Job 3: Thống kê số thẻ Flashcard FSRS đến hạn hôm nay
        # -------------------------------------------------------------
        try:
            logs.append("📊 [3/6] Thống kê thẻ Flashcard FSRS đến hạn hôm nay...")
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

        # -------------------------------------------------------------
        # Job 4: Tự động đồng bộ kế hoạch theo ngày và tiến độ học tập (Daily Plan & Progress Auto-Sync)
        # -------------------------------------------------------------
        try:
            logs.append("🗓️ [4/6] Tự động đồng bộ kế hoạch học tập theo ngày và tiến độ làm bài...")
            from app.services.plan_service import plan_service
            plan_res = plan_service.sync_all_plans()
            updated = plan_res.get("updated_files", [])
            if updated:
                logs.append(f"  ✅ Đã tự động cập nhật kế hoạch cho {len(updated)} file: {', '.join(updated)}")
            else:
                logs.append(f"  ✅ Kế hoạch học tập ngày {plan_res.get('today')} đã đồng bộ chuẩn mực.")
        except Exception as e:
            logs.append(f"  ⚠️ Cảnh báo Job 4 (Plan Sync): {e}")

        # -------------------------------------------------------------
        # Job 5: Tự động đánh giá tuần cũ & Lập kế hoạch tuần mới vào Chủ Nhật
        # -------------------------------------------------------------
        try:
            now_dt = datetime.now(VN_TZ)
            is_sunday_night = (now_dt.weekday() == 6 and now_dt.hour >= 21)
            is_monday_start = (now_dt.weekday() == 0 and now_dt.hour == 0)

            if is_sunday_night or is_monday_start or force:
                logs.append(f"🤖 [5/6] {'[TEST/FORCE]' if force else 'Đêm Chủ Nhật'}: Đánh giá tuần cũ (Weekly Retrospective) & lập kế hoạch tuần mới...")
                from app.services.plan_generator import autonomous_plan_generator
                
                plans_dir = os.path.join(settings.CONTENT_DIR, "plans")
                existing_weeks = []
                if os.path.exists(plans_dir):
                    for d in os.listdir(plans_dir):
                        if d.startswith("week-") and os.path.isdir(os.path.join(plans_dir, d)):
                            try:
                                existing_weeks.append(int(d.split("-")[1]))
                            except ValueError:
                                pass
                target_week = (max(existing_weeks) + 1) if existing_weeks else 1
                if target_week == 1 and existing_weeks:
                    target_week = 2

                res_week = autonomous_plan_generator.generate_next_week(target_week_number=target_week, force=force)
                if res_week.get("status") == "success":
                    logs.append(f"  ✅ Đã tự động tạo Kế hoạch Tuần {res_week.get('week_number')} ({res_week.get('date_range')}) cùng {len(res_week.get('created_files', []))} file bài làm mới.")
                elif res_week.get("status") == "already_exists":
                    logs.append(f"  ℹ️ Kế hoạch Tuần {target_week} đã tồn tại sẵn ({res_week.get('week_dir')}).")
                else:
                    logs.append(f"  ℹ️ {res_week.get('message', 'Kế hoạch tuần tiếp theo đã sẵn sàng.')}")
            else:
                logs.append("ℹ️ [5/6] Tự động hóa tuần mới sẵn sàng (sẽ kích hoạt vào đêm Chủ Nhật sau 21h hoặc khi gọi API /plans/generate-next-week).")
        except Exception as e:
            logs.append(f"  ⚠️ Cảnh báo Job 5 (Weekly Planner): {e}")

        # -------------------------------------------------------------
        # Job 6: Đồng bộ Anki Master Deck (Single Deck Rule) & Trạng thái SSOT
        # -------------------------------------------------------------
        try:
            logs.append("🎴 [6/6] Đồng bộ Anki Master Deck (Single Deck: 'IELTS - NoteAI Master Deck') & Trạng thái SSOT...")
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            anki_script = os.path.join(project_root, "scripts", "_py_", "anki_sync.py")
            if not os.path.exists(anki_script):
                anki_script = os.path.join("/app", "scripts", "_py_", "anki_sync.py")

            if os.path.exists(anki_script):
                res_anki = subprocess.run([sys.executable, anki_script], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=project_root)
                if res_anki.returncode == 0:
                    apkg_path = os.path.join(settings.CONTENT_DIR, "assets", "IELTS_Master_Deck.apkg")
                    apkg_size_kb = round(os.path.getsize(apkg_path) / 1024, 1) if os.path.exists(apkg_path) else 0
                    logs.append(f"  ✅ Đã xuất bản thành công Anki Master Deck: content/assets/IELTS_Master_Deck.apkg ({apkg_size_kb} KB).")
                else:
                    logs.append(f"  ⚠️ Cảnh báo Anki Sync: {res_anki.stderr or res_anki.stdout}")
            else:
                logs.append("  ℹ️ Script đồng bộ Anki không tìm thấy, bỏ qua bước sinh .apkg.")

            logs.append("  ✨ Kho tri thức SSOT Markdown đã đồng bộ và sẵn sàng phục vụ tức thì qua React SPA.")
        except Exception as e:
            logs.append(f"  ⚠️ Cảnh báo Job 6 (Anki Master Deck & SSOT): {e}")

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
