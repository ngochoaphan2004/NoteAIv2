import os
import re
import glob
import logging
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

        # Lấy danh sách các bài thi đã làm từ PostgreSQL
        completed_skills_and_files = set()
        with Session(engine) as session:
            attempts = session.exec(select(TestAttempt)).all()
            for att in attempts:
                if att.source_file:
                    clean_sf = att.source_file.strip("/").replace("\\", "/")
                    completed_skills_and_files.add(clean_sf)
                    completed_skills_and_files.add(os.path.basename(clean_sf).replace(".md", ""))
                if att.skill:
                    completed_skills_and_files.add(att.skill.lower())

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

    def _sync_single_week_file(
        self,
        file_path: str,
        today: date,
        completed_set: set
    ) -> bool:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        range_match = re.search(r"(\d{1,2})/(\d{1,2})\s*[-–]\s*(\d{1,2})/(\d{1,2})", content)
        if not range_match:
            return False

        start_d, start_m, end_d, end_m = map(int, range_match.groups())
        year = today.year
        start_date = date(year, start_m, start_d)
        end_date = date(year, end_m, end_d)

        is_current_week = (start_date <= today <= end_date)

        lines = content.splitlines()
        new_lines = []
        in_schedule_table = False
        today_task_info = None
        day_index = 1

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
                # Dùng regex (?<!\\)\| để KHÔNG cắt nhầm ký tự escaped \| trong bảng
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

                        # Tìm link trong col_focus (ví dụ: [[plans/week-01/test-1-listening\|...]])
                        link_match = re.search(r"\[\[([^\\|\]]+)", col_focus)
                        file_key = ""
                        if link_match:
                            file_key = os.path.basename(link_match.group(1)).replace(".md", "")

                        is_done = (
                            (file_key and file_key in completed_set) or
                            ("listening" in col_skill.lower() and "listening" in completed_set) or
                            ("reading" in col_skill.lower() and "reading" in completed_set)
                        )

                        clean_day_name = col_day.split("<br>")[0].replace("**", "").replace("(Hôm nay)", "").strip()

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

                        parts[1] = new_col_day
                        parts[4] = new_col_status
                        line = "| " + " | ".join(parts[1:5]) + " |"
                        day_index += 1

            new_lines.append(line)

        content = "\n".join(new_lines)

        # 2. Cập nhật Dòng trạng thái tuần (line 18)
        if today_task_info and is_current_week:
            status_line_regex = r">\s*\*\*Trạng thái tuần:\*\*.*"
            new_status_line = (
                f"> **Trạng thái tuần:** Đang diễn ra — Ngày {today_task_info['day_index']} "
                f"(Hôm nay: {today_task_info['day_name']}, {today_task_info['date_str']})"
            )
            content = re.sub(status_line_regex, new_status_line, content)

            # 3. Cập nhật Mục 2: "Chi Tiết Nhiệm Vụ Hôm Nay"
            section2_regex = r"(## 📝 2\. Chi Tiết Nhiệm Vụ Hôm Nay:)[^\n]*\n([\s\S]*?)(?=\n## 🔗 3\.|\Z)"
            
            # Format skill title
            skill_text = re.sub(r"<[^>]+>", " — ", today_task_info["skill"]).replace("**", "").replace("`", "").strip()
            focus_clean = today_task_info["focus"]
            checked_box = "[x]" if today_task_info["is_done"] else "[ ]"

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
                if b.startswith("👉"):
                    continue
                clean_b = b.lstrip("•").strip()
                clean_bullets.append(f"- {checked_box} {clean_b}")
            bullet_md = "\n".join(clean_bullets)

            task_section_content = f"""
### 🎯 {skill_text}

{bullet_md}
- {checked_box} **Nộp bài cho AI:** Hoàn thành các câu hỏi trên bảng tương tác và nhấn nút _"🚀 Gửi Câu Trả Lời Cho AI"_.
{f"- 🔗 **Mở bài làm chi tiết:** 👉 {link_display}" if link_display else ""}
- 💡 **Nguyên tắc:** Mỗi phiên cố định 30–35 phút để đảm bảo Cognitive Load Control.
"""
            replacement_header = f"## 📝 2. Chi Tiết Nhiệm Vụ Hôm Nay: {today_task_info['day_name']} ({today_task_info['date_str']})\n"
            content = re.sub(section2_regex, replacement_header + task_section_content, content)

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
                # Tìm dòng của hôm nay trong bảng
                lines = content.splitlines()
                for line in lines:
                    if line.startswith("|") and today.strftime("%d/%m") in line:
                        parts = [p.strip() for p in re.split(r"(?<!\\)\|", line)]
                        if len(parts) >= 6:
                            skill = re.sub(r"<[^>]+>", " ", parts[2]).replace("**", "").strip()
                            focus = parts[3]
                            status = parts[4]
                            is_done = "Đã" in status or "✅" in status

                            link_match = re.search(r"\[\[([^\\|\]]+)", focus)
                            link_path = link_match.group(1) if link_match else ""

                            return {
                                "today": today_info["formatted_full"],
                                "week": os.path.basename(os.path.dirname(week_file)),
                                "skill": skill,
                                "focus": focus.split("👉")[0].strip(),
                                "link": link_path,
                                "is_done": is_done,
                                "status": status
                            }

        return {
            "today": today_info["formatted_full"],
            "week": None,
            "skill": "Ôn tập FSRS Flashcards",
            "focus": "Hoàn thành toàn bộ thẻ nhớ đến hạn hôm nay.",
            "link": "",
            "is_done": False,
            "status": "🎯 Hôm nay"
        }

plan_service = PlanService()
