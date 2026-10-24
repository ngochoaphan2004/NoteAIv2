import os
import re
import glob
import logging
import subprocess
import threading
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.models.test_attempt import TestAttempt

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
logger = logging.getLogger("plan_service")

DAY_NAMES_VI = {
    0: "Thứ 2",
    1: "Thứ 3",
    2: "Thứ 4",
    3: "Thứ 5",
    4: "Thứ 6",
    5: "Thứ 7",
    6: "Chủ Nhật"
}

class PlanService:
    """
    Dịch vụ Tự Động Quản Lý Kế Hoạch & Tiến Độ Học Tập Cá Nhân (Autonomous Plan & Progress Service)
    - Tự động nhận diện ngày hiện tại (múi giờ UTC+7 Việt Nam).
    - Tự động đối chiếu với CSDL PostgreSQL (tiến độ bài làm, điểm số, lỗi sai).
    - Tự động cập nhật file Markdown kế hoạch tuần (bảng tiến độ, nhiệm vụ hôm nay, checklist).
    - Cung cấp API cho Frontend hiển thị nhiệm vụ ngày hôm nay.
    """

    def get_current_vn_time(self) -> datetime:
        return datetime.now(VN_TZ)

    def get_today_info(self, ref_dt: Optional[datetime] = None) -> Dict[str, Any]:
        dt = ref_dt or self.get_current_vn_time()
        day_vi = DAY_NAMES_VI.get(dt.weekday(), "Thứ 2")
        return {
            "date": dt.date(),
            "day_name": day_vi,
            "formatted_short": dt.strftime("%d/%m"),
            "formatted_full": f"{day_vi}, {dt.strftime('%d/%m/%Y')}",
            "year": dt.year,
            "month": dt.month,
            "day": dt.day
        }

    def sync_all_plans(self, ref_dt: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Quét toàn bộ thư mục content/plans/ và tự động đồng bộ file kế hoạch tuần hiện tại.
        """
        now = ref_dt or self.get_current_vn_time()
        today = now.date()
        content_dir = settings.CONTENT_DIR
        plans_dir = os.path.join(content_dir, "plans")

        if not os.path.exists(plans_dir):
            logger.warning(f"Thư mục kế hoạch không tồn tại: {plans_dir}")
            return {"status": "error", "message": "Plans directory not found"}

        week_files = sorted(glob.glob(os.path.join(plans_dir, "week-*", "index.md")))
        updated_files = []

        # Lấy danh sách các bài thi đã làm từ PostgreSQL (có fallback nếu DB offline)
        completed_skills_and_files = set()
        try:
            with Session(engine) as session:
                attempts = session.exec(select(TestAttempt)).all()
                for att in attempts:
                    if att.source_file:
                        clean_sf = att.source_file.strip("/").replace("\\", "/")
                        completed_skills_and_files.add(clean_sf)
                        completed_skills_and_files.add(os.path.basename(clean_sf).replace(".md", ""))
        except Exception as db_err:
            logger.warning(f"Không thể truy vấn CSDL PostgreSQL cho lịch sử bài thi: {db_err}")

        for week_file in week_files:
            try:
                changed = self._sync_single_week_file(week_file, today, completed_skills_and_files)
                if changed:
                    updated_files.append(os.path.relpath(week_file, content_dir))
            except Exception as e:
                logger.error(f"Lỗi khi đồng bộ file kế hoạch {week_file}: {e}", exc_info=True)

        logger.info(f"[PLAN SYNC] Hoàn tất đồng bộ kế hoạch ngày {today.strftime('%d/%m/%Y')}. File cập nhật: {len(updated_files)}")
        return {
            "status": "success",
            "today": today.strftime("%d/%m/%Y"),
            "updated_files": updated_files
        }

    def _is_task_completed(
        self,
        week_dir: str,
        file_key: str,
        col_skill: str,
        completed_set: set
    ) -> bool:
        """
        Xác định một nhiệm vụ đã hoàn thành hay chưa bằng cả CSDL (PostgreSQL)
        và tệp Markdown thực tế trên đĩa (SSOT - Single Source of Truth).
        """
        if file_key and file_key in completed_set:
            return True

        if file_key:
            md_path = os.path.join(week_dir, f"{file_key}.md")
            if not os.path.exists(md_path):
                md_path = os.path.join(settings.CONTENT_DIR, f"{file_key}.md")

            if os.path.exists(md_path):
                try:
                    with open(md_path, "r", encoding="utf-8") as f:
                        text = f.read()

                    # 1. Writing Task
                    if "writing" in file_key:
                        m_words = re.search(r"Lưu Trữ Nguyên Bản\s*-\s*(\d+)\s*từ", text)
                        if m_words and int(m_words.group(1)) > 0:
                            return True
                        m_txt = re.search(r"<textarea[^>]*>([\s\S]*?)</textarea>", text)
                        if m_txt and len(m_txt.group(1).strip()) > 30:
                            return True
                        if "Bài Làm Thực Tế" in text:
                            body_after = text.split("Bài Làm Thực Tế")[-1]
                            if "Chưa nộp bài" not in body_after and len(body_after.strip()) > 50:
                                return True
                        return False

                    # 2. Listening & Reading Test
                    if "test" in file_key and ("listening" in file_key or "reading" in file_key):
                        for line in text.splitlines():
                            if re.match(r"^\|\s*\*\*\d+\*\*\s*\|", line):
                                cols = [c.strip() for c in line.split("|")]
                                if len(cols) >= 3:
                                    ans = cols[2].replace("`", "").strip()
                                    if ans and ans != "[ ]" and ans != "_(chờ điền)_" and not ans.startswith("..."):
                                        return True
                        return False

                    # 3. Flashcards & Vocab
                    if "vocab" in file_key:
                        if "✅ Đã ôn tập" in text or "Đã hoàn thành" in text:
                            return True
                        return False

                except Exception as e:
                    logger.warning(f"Lỗi kiểm tra trạng thái file {md_path}: {e}")

        return False

    def _sync_single_week_file(
        self,
        file_path: str,
        today: date,
        completed_set: set
    ) -> bool:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        week_dir = os.path.dirname(file_path)

        range_match = re.search(r"(\d{1,2})/(\d{1,2})\s*[-–]\s*(\d{1,2})/(\d{1,2})", content)
        if not range_match:
            return False

        start_d, start_m, end_d, end_m = map(int, range_match.groups())
        year = today.year
        start_date = date(year, start_m, start_d)
        end_date = date(year, end_m, end_d)

        is_current_week = (start_date <= today <= end_date)
        is_past_week = (today > end_date)
        is_future_week = (today < start_date)

        lines = content.splitlines()
        new_lines = []
        in_schedule_table = False
        today_task_info = None
        first_upcoming_task = None
        day_index = 1
        first_day_name = "Thứ 2"

        for line in lines:
            if "## 🗓️ 1. Bảng Tổng Quan Lịch Trình Tuần" in line:
                in_schedule_table = True
                new_lines.append(line)
                continue

            if in_schedule_table and line.startswith("---"):
                in_schedule_table = False
                new_lines.append(line)
                continue

            if in_schedule_table and line.startswith("|") and not line.startswith("| :---"):
                raw_parts = re.split(r"(?<!\\)\|", line)
                parts = [p.strip() for p in raw_parts]

                # Bảng có 4 cột chính: [ "", Cột 1, Cột 2, Cột 3, Cột 4, "" ]
                if len(parts) >= 6 and any(d in parts[1] for d in ["Thứ", "Chủ Nhật"]):
                    col_day = parts[1]
                    col_skill = parts[2]
                    col_focus = parts[3]
                    col_status = parts[4]

                    date_match = re.search(r"(\d{1,2})/(\d{1,2})", col_day)
                    if date_match:
                        row_d, row_m = map(int, date_match.groups())
                        row_date = date(year, row_m, row_d)

                        # Trích xuất link / file_key từ col_focus
                        link_match = re.search(r"\[\[([^\\|\]]+)", col_focus)
                        file_key = ""
                        if link_match:
                            file_key = os.path.basename(link_match.group(1)).replace(".md", "")

                        # Kiểm tra tiến độ hoàn thành từ DB và Markdown SSOT
                        is_done = self._is_task_completed(week_dir, file_key, col_skill, completed_set)

                        clean_day_name = col_day.split("<br>")[0].replace("**", "").replace("(Hôm nay)", "").strip()
                        if day_index == 1:
                            first_day_name = clean_day_name

                        if row_date < today:
                            new_col_day = f"**{clean_day_name}**<br>_({row_d:02d}/{row_m:02d}/{year})_"
                            new_col_status = "✅ **Đã hoàn thành**" if is_done else "⏳ **Cần hoàn thành bù**"
                        elif row_date == today:
                            new_col_day = f"**{clean_day_name} (Hôm nay)**<br>_({row_d:02d}/{row_m:02d}/{year})_"
                            new_col_status = "✅ **Đã xong hôm nay**" if is_done else "🎯 **Hôm nay**"

                            today_task_info = {
                                "day_name": clean_day_name,
                                "date_str": f"{row_d:02d}/{row_m:02d}/{year}",
                                "skill": col_skill,
                                "focus": col_focus,
                                "is_done": is_done,
                                "file_key": file_key,
                                "day_index": day_index
                            }
                        else:
                            new_col_day = f"**{clean_day_name}**<br>_({row_d:02d}/{row_m:02d}/{year})_"
                            new_col_status = "[ ] Sắp tới"

                            if first_upcoming_task is None:
                                first_upcoming_task = {
                                    "day_name": clean_day_name,
                                    "date_str": f"{row_d:02d}/{row_m:02d}/{year}",
                                    "skill": col_skill,
                                    "focus": col_focus,
                                    "is_done": is_done,
                                    "file_key": file_key,
                                    "day_index": day_index
                                }

                        parts[1] = new_col_day
                        parts[4] = new_col_status
                        line = "| " + " | ".join(parts[1:5]) + " |"
                        day_index += 1

            new_lines.append(line)

        content = "\n".join(new_lines)

        # 2. Cập nhật Dòng trạng thái tuần
        status_line_regex = r">\s*\*\*Trạng thái tuần:\*\*.*"
        if is_current_week and today_task_info:
            new_status_line = (
                f"> **Trạng thái tuần:** Đang diễn ra — Ngày {today_task_info['day_index']} "
                f"(Hôm nay: {today_task_info['day_name']}, {today_task_info['date_str']})"
            )
            content = re.sub(status_line_regex, new_status_line, content)
        elif is_past_week:
            new_status_line = f"> **Trạng thái tuần:** Đã kết thúc trọn vẹn ({start_d:02d}/{start_m:02d} – {end_d:02d}/{end_m:02d}/{year})"
            content = re.sub(status_line_regex, new_status_line, content)
        elif is_future_week:
            new_status_line = f"> **Trạng thái tuần:** Sắp diễn ra — Khởi động vào {first_day_name} ({start_d:02d}/{start_m:02d}/{year})"
            content = re.sub(status_line_regex, new_status_line, content)

        # 3. Cập nhật Mục 2: "Chi Tiết Nhiệm Vụ Hôm Nay / Mở Màn"
        section2_regex = r"## 📝 2\.[^\n]*\n([\s\S]*?)(?=\n## 🔗 3\.|\Z)"

        target_task = None
        header_title = None

        if is_current_week and today_task_info:
            target_task = today_task_info
            header_title = f"## 📝 2. Chi Tiết Nhiệm Vụ Hôm Nay: {target_task['day_name']} ({target_task['date_str']})"
        elif is_future_week and first_upcoming_task:
            target_task = first_upcoming_task
            header_title = f"## 📝 2. Nhiệm Vụ Mở Màn Sắp Tới: {target_task['day_name']} ({target_task['date_str']})"

        if target_task and header_title and re.search(section2_regex, content):
            skill_text = re.sub(r"<[^>]+>", " — ", target_task["skill"]).replace("**", "").replace("`", "").strip()
            focus_clean = target_task["focus"]
            checked_box = "[x]" if target_task["is_done"] else "[ ]"

            # Trích xuất link chi tiết từ focus
            link_display = ""
            link_match = re.search(r"\[\[([^\\|\]]+)(?:\\?\|([^\]]+))?\]\]", focus_clean)
            if link_match:
                raw_path = link_match.group(1).strip()
                text_part = link_match.group(2) or raw_path
                link_display = f"[[{raw_path}|{text_part.strip()}]]"

            # Trích xuất bullet points từ focus
            bullets = [b.strip() for b in focus_clean.split("<br>") if b.strip()]
            clean_bullets = []
            for b in bullets:
                if b.startswith("👉") or b.startswith("[["):
                    continue
                clean_b = b.split("👉")[0].strip().lstrip("•").strip()
                if clean_b:
                    clean_bullets.append(f"- {checked_box} {clean_b}")

            body_lines = ["", f"### 🎯 {skill_text}", ""]
            if clean_bullets:
                body_lines.extend(clean_bullets)
            if link_display:
                body_lines.append(f"- {checked_box} **Nộp bài cho AI:** Hoàn thành các câu hỏi trên bảng tương tác và nhấn nút _\"🚀 Nộp Bài & Chấm Điểm Trực Tiếp\"_.")
                body_lines.append(f"- 🔗 **Mở bài làm chi tiết:** 👉 {link_display}")
            else:
                body_lines.append(f"- {checked_box} **Thực hành & Tự đánh giá:** Hoàn thành bài luyện tập theo thời lượng quy định và ghi chú lại khó khăn.")
            body_lines.append("- 💡 **Nguyên tắc:** Mỗi phiên cố định 30–35 phút để đảm bảo Cognitive Load Control.")
            body_lines.append("")

            full_section_2 = f"{header_title}\n" + "\n".join(body_lines)
            content = re.sub(section2_regex, full_section_2, content)

        content = content.rstrip("\n") + "\n"
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    def mark_task_attempt(
        self,
        skill: str,
        source_file: Optional[str] = None
    ) -> bool:
        logger.info(f"[PLAN SYNC] Ghi nhận bài nộp skill='{skill}', source='{source_file}'. Đồng bộ lại kế hoạch...")
        res = self.sync_all_plans()
        if res.get("updated_files"):
            threading.Thread(target=rebuild_quartz, daemon=True).start()
        return len(res.get("updated_files", [])) > 0

    def get_today_task_summary(self) -> Dict[str, Any]:
        """Trả về thông tin nhiệm vụ ngày hôm nay cho React SPA Frontend"""
        now = self.get_current_vn_time()
        today = now.date()
        today_info = self.get_today_info(now)

        content_dir = settings.CONTENT_DIR
        plans_dir = os.path.join(content_dir, "plans")
        week_files = sorted(glob.glob(os.path.join(plans_dir, "week-*", "index.md")))

        for week_file in week_files:
            with open(week_file, "r", encoding="utf-8") as f:
                content = f.read()

            range_match = re.search(r"(\d{1,2})/(\d{1,2})\s*[-–]\s*(\d{1,2})/(\d{1,2})", content)
            if not range_match:
                continue

            start_d, start_m, end_d, end_m = map(int, range_match.groups())
            year = today.year
            start_date = date(year, start_m, start_d)
            end_date = date(year, end_m, end_d)

            if start_date <= today <= end_date:
                week_name = os.path.basename(os.path.dirname(week_file))

                # Cơ chế Tự Phục Hồi (Self-Healing):
                # Nếu file kế hoạch tuần chưa được chuyển trạng thái sang ngày hôm nay, tự động sync ngay lập tức
                today_tag = f"Hôm nay: {today_info['formatted_full']}"
                if today_tag not in content:
                    logger.info(f"[PLAN SELF-HEAL] Phát hiện kế hoạch chưa đồng bộ ngày {today_info['formatted_full']}. Tự động đồng bộ ngay...")
                    self.sync_all_plans()
                    with open(week_file, "r", encoding="utf-8") as f:
                        content = f.read()

                # Tìm dòng của hôm nay trong bảng
                lines = content.splitlines()
                for line in lines:
                    if line.startswith("|") and not line.startswith("| :---"):
                        parts = [p.strip() for p in re.split(r"(?<!\\)\|", line)]
                        if len(parts) >= 6 and any(d in parts[1] for d in ["Thứ", "Chủ Nhật"]):
                            date_match = re.search(r"(\d{1,2})/(\d{1,2})", parts[1])
                            if not date_match:
                                continue
                            row_d, row_m = map(int, date_match.groups())
                            if date(year, row_m, row_d) != today:
                                continue

                            raw_skill = parts[2]
                            duration_match = re.search(r"`([^`]+)`", raw_skill)
                            if not duration_match:
                                duration_match = re.search(r"(\d+\s*phút)", raw_skill)
                            duration = duration_match.group(1).strip() if duration_match else "35 phút"

                            clean_skill = re.sub(r"<[^>]+>", " ", raw_skill)
                            clean_skill = re.sub(r"`[^`]*`", "", clean_skill)
                            clean_skill = clean_skill.replace("**", "").strip()

                            raw_focus = parts[3]
                            status = parts[4]
                            is_done = "Đã" in status or "✅" in status

                            link_match = re.search(r"\[\[([^\\|\]]+)", raw_focus)
                            link_path = link_match.group(1) if link_match else f"plans/{week_name}/"

                            # Xử lý steps sạch sẽ
                            raw_steps = [s.strip() for s in raw_focus.split("<br>") if s.strip()]
                            clean_steps = []
                            for s in raw_steps:
                                if s.startswith("👉") or s.startswith("[["):
                                    continue
                                s_clean = s.split("👉")[0].strip()
                                s_clean = s_clean.lstrip("•").strip()
                                s_clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", s_clean)
                                s_clean = re.sub(r"_([^_]+)_", r"\1", s_clean)
                                s_clean = re.sub(r"`([^`]+)`", r"\1", s_clean)
                                s_clean = s_clean.strip()
                                if s_clean:
                                    clean_steps.append(s_clean)

                            clean_focus = " • ".join(clean_steps) if clean_steps else raw_focus.split("👉")[0].strip()

                            return {
                                "today": today_info["formatted_full"],
                                "week": week_name,
                                "skill": clean_skill,
                                "duration": duration,
                                "focus": clean_focus,
                                "steps": clean_steps,
                                "link": link_path,
                                "is_done": is_done,
                                "status": status
                            }

        return {
            "today": today_info["formatted_full"],
            "week": None,
            "skill": "Ôn tập FSRS Flashcards",
            "duration": "15 phút",
            "focus": "Hoàn thành toàn bộ thẻ nhớ đến hạn hôm nay.",
            "steps": ["Hoàn thành toàn bộ thẻ nhớ đến hạn hôm nay."],
            "link": "",
            "is_done": False,
            "status": "🎯 Hôm nay"
        }

plan_service = PlanService()


_quartz_build_lock = threading.Lock()


def rebuild_quartz(detailed: bool = False) -> Any:
    """
    Tự động biên dịch lại Quartz HTML tĩnh vào thư mục public/ sử dụng 'npm run quartz -- build'.
    Hỗ trợ fallback sang 'node ./quartz/bootstrap-cli.mjs build' và 'npx quartz build'.
    Sử dụng non-blocking lock để tránh chạy chồng chéo nhiều tiến trình build cùng lúc.
    """
    acquired = _quartz_build_lock.acquire(blocking=False)
    if not acquired:
        logger.info("[QUARTZ BUILD] Tiến trình biên dịch Quartz khác đang chạy. Bỏ qua yêu cầu trùng lặp.")
        return {"success": True, "message": "Build already in progress"} if detailed else True

    try:
        content_dir = settings.CONTENT_DIR
        candidate_roots = [
            os.path.dirname(os.path.abspath(content_dir)),
            "/opt/noteai",
            os.getcwd()
        ]
        root_dir = None
        for cand in candidate_roots:
            if cand and os.path.exists(os.path.join(cand, "quartz.config.ts")):
                root_dir = cand
                break

        if not root_dir:
            logger.warning("[QUARTZ BUILD] Không tìm thấy thư mục cấu hình quartz.config.ts. Bỏ qua rebuild.")
            return {"success": False, "error": "quartz.config.ts not found"} if detailed else False

        is_windows = (os.name == "nt")
        npm_bin = "npm.cmd" if is_windows else "npm"
        npx_bin = "npx.cmd" if is_windows else "npx"

        commands_to_try = [
            ([npm_bin, "run", "quartz", "--", "build"], "npm run quartz -- build"),
            (["node", "./quartz/bootstrap-cli.mjs", "build"], "node ./quartz/bootstrap-cli.mjs build"),
            ([npx_bin, "quartz", "build"], "npx quartz build")
        ]

        last_error = ""
        for cmd, cmd_str in commands_to_try:
            try:
                logger.info(f"[QUARTZ BUILD] Đang thực thi lệnh '{cmd_str}' tại {root_dir}...")
                res = subprocess.run(cmd, cwd=root_dir, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    logger.info(f"[QUARTZ BUILD] Thành công 100% qua lệnh '{cmd_str}'! Toàn bộ file Markdown đã được biên dịch vào public/.")
                    # Đảm bảo symlink audio được duy trì sau khi build làm sạch public
                    audio_src = os.path.join(content_dir, "assets", "audio")
                    audio_dst = os.path.join(root_dir, "public", "assets", "audio")
                    if os.path.exists(audio_src) and not os.path.exists(audio_dst):
                        try:
                            os.makedirs(os.path.dirname(audio_dst), exist_ok=True)
                            if not is_windows:
                                os.symlink(audio_src, audio_dst)
                        except Exception as e:
                            logger.warning(f"[QUARTZ BUILD] Không thể tạo symlink audio: {e}")
                    return {"success": True, "command": cmd_str, "output": res.stdout[-300:]} if detailed else True
                else:
                    last_error = res.stderr or res.stdout
                    logger.warning(f"[QUARTZ BUILD] Lệnh '{cmd_str}' thoát với mã {res.returncode}: {last_error[:200]}")
            except FileNotFoundError as fnf:
                last_error = str(fnf)
                logger.warning(f"[QUARTZ BUILD] Không tìm thấy file chạy cho '{cmd_str}': {fnf}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[QUARTZ BUILD] Ngoại lệ khi thực thi '{cmd_str}': {e}")

        logger.error(f"[QUARTZ BUILD] Toàn bộ các phương thức biên dịch đều thất bại. Lỗi cuối: {last_error}")
        return {"success": False, "error": last_error} if detailed else False
    except Exception as general_err:
        logger.error(f"[QUARTZ BUILD] Ngoại lệ tổng quát trong rebuild_quartz: {general_err}")
        return {"success": False, "error": str(general_err)} if detailed else False
    finally:
        _quartz_build_lock.release()

