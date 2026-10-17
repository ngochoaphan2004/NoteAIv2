import os
import re
import json
import logging
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.models.test_attempt import TestAttempt, QuestionAnalysis
from app.models.flashcard import Flashcard
from app.services.llm_service import llm_service
from app.services.plan_service import rebuild_quartz

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
logger = logging.getLogger("plan_generator")

DAY_NAMES_VI = {
    0: "Thứ 2",
    1: "Thứ 3",
    2: "Thứ 4",
    3: "Thứ 5",
    4: "Thứ 6",
    5: "Thứ 7",
    6: "Chủ Nhật"
}

class AutonomousPlanGenerator:
    """
    Autonomous Planning & Retrospective Engine cho NoteAI.v2.
    1. Đánh giá kết quả tuần cũ (Weekly Retrospective) từ CSDL PostgreSQL (bài làm, bẫy âm, từ vựng).
    2. LLM Gemini tổng kết điểm mạnh, lỗ hổng cần khắc phục và chiến lược micro-sessions thích ứng.
    3. Tự động tính toán chu kỳ tuần mới theo Quy tắc Chu Kỳ Kế Hoạch Tuần (kết thúc Chủ Nhật).
    4. Trích xuất tài nguyên hình ảnh sách gốc từ content/assets/book_pages_web_ready.json.
    5. Tự động sinh ra cấu trúc thư mục tuần mới:
       - content/plans/week-XX/index.md (Hub kế hoạch tuần, bảng micro-sessions, checklist, retrospective)
       - test-X-listening.md (Đề gốc, audio script, bảng tương tác, đối soát)
       - test-X-reading-p3.md (Passage 3, keyword mapping, đối soát)
       - test-X-writing.md (Task 1 & Task 2 prompts, scaffolding, split-screen workspace)
       - vocab-week-XX.md (Sổ từ vựng trọng tâm FSRS/Anki)
    6. Cập nhật liên kết cấp macro tại content/plans/index.md và content/index.md.
    """

    def __init__(self):
        self.content_dir = settings.CONTENT_DIR
        self.book_assets_file = os.path.join(self.content_dir, "assets", "book_pages_web_ready.json")
        self.audio_assets_file = os.path.join(self.content_dir, "assets", "audio_metadata.json")
        self._book_cache: Optional[Dict[str, Any]] = None
        self._audio_cache: Optional[Dict[str, Any]] = None

    def _get_book_assets(self) -> Dict[str, Any]:
        if self._book_cache is None:
            if os.path.exists(self.book_assets_file):
                with open(self.book_assets_file, "r", encoding="utf-8") as f:
                    self._book_cache = json.load(f)
            else:
                self._book_cache = {"structured_tree": [], "pages": []}
        return self._book_cache

    def _get_audio_assets(self) -> Dict[str, Any]:
        if self._audio_cache is None:
            if os.path.exists(self.audio_assets_file):
                try:
                    with open(self.audio_assets_file, "r", encoding="utf-8") as f:
                        self._audio_cache = json.load(f)
                except Exception as e:
                    logger.warning(f"Lỗi khi đọc file audio_metadata.json: {e}")
                    self._audio_cache = {"tests": {}}
            else:
                self._audio_cache = {"tests": {}}
        return self._audio_cache

    def get_test_audio_data(self, test_number: int) -> Dict[str, Any]:
        """Trích xuất metadata các file audio tương ứng cho Test N từ audio_metadata.json"""
        audio_db = self._get_audio_assets()
        return audio_db.get("tests", {}).get(str(test_number), {})

    def get_cambridge_test_data(self, test_number: int) -> Dict[str, Any]:
        """Trích xuất toàn bộ metadata và URL ảnh các trang cho Test N từ sách Cambridge 18"""
        book = self._get_book_assets()
        test_id = f"test_{test_number}"
        test_meta = None
        for t in book.get("structured_tree", []):
            if t.get("test_id") == test_id:
                test_meta = t
                break

        pages_by_num = {p["page_number"]: p for p in book.get("pages", [])}

        listening_pages = []
        reading_pages = []
        writing_pages = []
        speaking_pages = []

        if test_meta:
            for skill in test_meta.get("skills", []):
                s_id = skill.get("skill_id")
                for phase in skill.get("phases", []):
                    p_start = phase.get("page_start", 0)
                    p_end = phase.get("page_end", 0)
                    for pn in range(p_start, p_end + 1):
                        p_data = pages_by_num.get(pn)
                        if p_data:
                            entry = {
                                "page_number": pn,
                                "title": p_data.get("title", phase.get("title")),
                                "phase_name": phase.get("title"),
                                "topic": phase.get("topic"),
                                "questions": phase.get("questions"),
                                "url": p_data.get("image", {}).get("url")
                            }
                            if s_id == "listening":
                                listening_pages.append(entry)
                            elif s_id == "reading":
                                reading_pages.append(entry)
                            elif s_id == "writing":
                                writing_pages.append(entry)
                            elif s_id == "speaking":
                                speaking_pages.append(entry)

        # Trích xuất audioscript tương ứng cho Test N
        audioscript_pages = []
        # Cambridge 18: Test 1 (101-105), Test 2 (106-110), Test 3 (111-115), Test 4 (116-120)
        audio_start = 101 + (test_number - 1) * 5
        audio_end = audio_start + 4
        for pn in range(audio_start, audio_end + 1):
            p_data = pages_by_num.get(pn)
            if p_data:
                audioscript_pages.append({
                    "page_number": pn,
                    "title": p_data.get("title", f"Audioscript Trang {pn}"),
                    "url": p_data.get("image", {}).get("url")
                })

        return {
            "test_number": test_number,
            "test_id": test_id,
            "meta": test_meta,
            "listening_pages": listening_pages,
            "reading_pages": reading_pages,
            "writing_pages": writing_pages,
            "speaking_pages": speaking_pages,
            "audioscript_pages": audioscript_pages
        }

    def evaluate_past_week(self, week_number: int) -> Dict[str, Any]:
        """
        Truy vấn PostgreSQL để bóc tách kết quả làm bài của tuần cũ,
        sau đó gọi LLM Gemini để viết bản nhận xét tổng kết tuần (Weekly Retrospective).
        """
        attempts_summary: List[Dict[str, Any]] = []
        trap_counts: Dict[str, int] = {}
        total_questions_done = 0
        total_correct = 0

        try:
            with Session(engine) as session:
                attempts = session.exec(select(TestAttempt)).all()
                for att in attempts:
                    att_dict = {
                        "title": att.title,
                        "skill": att.skill,
                        "score": att.score,
                        "total": att.total_questions,
                        "band_score": att.band_score,
                        "created_at": att.created_at.strftime("%Y-%m-%d %H:%M")
                    }
                    attempts_summary.append(att_dict)
                    if att.score and att.total_questions:
                        total_correct += att.score
                        total_questions_done += att.total_questions

                analyses = session.exec(select(QuestionAnalysis)).all()
                for q in analyses:
                    if q.trap_type:
                        trap_counts[q.trap_type] = trap_counts.get(q.trap_type, 0) + 1

                flashcards_total = len(session.exec(select(Flashcard)).all())
        except Exception as e:
            logger.warning(f"[PLAN GEN] Lỗi truy vấn PostgreSQL cho tuần cũ: {e}")
            flashcards_total = 0

        # Nếu chưa có bài làm nào trên DB, cung cấp thông số khởi điểm tuần 1
        has_real_data = len(attempts_summary) > 0
        overall_accuracy = round((total_correct / total_questions_done * 100), 1) if total_questions_done > 0 else 0

        # Gọi LLM sinh bản tổng kết tuần
        ai_retrospective_md = ""
        prompt = (
            f"Bạn là Chuyên gia Khảo thí và Lập Kế Hoạch Học Tập IELTS NoteAI.v2.\n"
            f"Nhiệm vụ: Viết bản nhận xét tổng kết tuần cũ (Tuần {week_number}) để bàn giao sang Tuần {week_number + 1}.\n"
            f"Dữ liệu thực tế: {attempts_summary if has_real_data else 'Tuần 1 khởi động làm quen nền tảng, tập trung bóc tách bẫy và luyện thói quen micro-sessions 30-35p'}.\n"
            f"Thống kê bẫy âm/lỗi sai: {trap_counts if trap_counts else 'Bẫy số đuôi -teen vs -ty, chia thì quá khứ đơn, nội động từ Writing Task 1'}.\n"
            f"Số thẻ từ vựng FSRS: {flashcards_total} thẻ.\n\n"
            f"Yêu cầu định dạng đầu ra (Markdown súc tích, chuyên nghiệp, không dài dòng):\n"
            f"1. **Tổng quan tiến độ (3 dòng)**: Đánh giá kỷ luật học tập và mức độ hoàn thành.\n"
            f"2. **Điểm sáng đã đạt (Bullet points)**: Các kỹ năng thực hiện tốt.\n"
            f"3. **Lỗ hổng & Bẫy âm cần khắc phục (Bullet points)**: Chỉ rõ lỗi ngữ pháp/bẫy đề thi.\n"
            f"4. **Chiến lược thích ứng cho Tuần {week_number + 1}**: Gợi ý các micro-sessions tập trung bù đắp."
        )
        system_prompt = (
            "Bạn là Chuyên gia Cố vấn IELTS NoteAI. Phân tích sắc bén, văn phong sư phạm động viên nhưng nghiêm túc, "
            "tuân thủ quy tắc Cognitive Load Control (phiên 30-35p)."
        )

        try:
            ai_retrospective_md = llm_service.generate_text(prompt, system_message=system_prompt)
        except Exception as e:
            logger.warning(f"[PLAN GEN] Lỗi gọi LLM cho Retrospective ({e}), tạo fallback.")
            ai_retrospective_md = (
                f"### 🎯 Tổng Kết Tiến Độ Tuần {week_number}\n\n"
                f"- **Kỷ luật học tập:** Đã duy trì nhịp độ làm quen các phiên Micro-sessions 30–35 phút.\n"
                f"- **Điểm sáng:** Nắm vững cấu trúc bảng đối soát và phương pháp nhập liệu Shorthand Syntax.\n"
                f"- **Lỗ hổng trọng tâm:** Cần củng cố phân biệt bẫy âm số đuôi `-teen` / `-ty` và quy tắc không chia bị động cho nội động từ trong Writing Task 1.\n"
                f"- **Định hướng Tuần {week_number + 1}:** Tăng tốc độ phản xạ Listening Part 2 & 3 và đẩy mạnh kỹ năng Keyword Mapping ở Reading Passage 3."
            )

        return {
            "week_number": week_number,
            "has_real_data": has_real_data,
            "total_attempts": len(attempts_summary),
            "total_questions_done": total_questions_done,
            "total_correct": total_correct,
            "accuracy_percent": overall_accuracy,
            "trap_counts": trap_counts,
            "flashcards_total": flashcards_total,
            "ai_retrospective_md": ai_retrospective_md
        }

    def generate_next_week(
        self,
        target_week_number: int = 2,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Tự động tạo tuần học mới (Ví dụ: Tuần 2: 19/10 – 25/10/2026):
        1. Đánh giá tuần cũ và cập nhật vào index.md của tuần trước.
        2. Tạo thư mục plans/week-02/.
        3. Tạo file index.md tuần mới với các micro-sessions thích ứng.
        4. Tự tạo các file Markdown bài làm cho từng ngày:
           - test-2-listening.md
           - test-2-reading-p3.md
           - test-2-writing.md
           - vocab-week-02.md
        5. Cập nhật links tại content/plans/index.md và content/index.md.
        6. Kích hoạt Quartz rebuild.
        """
        prev_week_number = target_week_number - 1
        plans_dir = os.path.join(self.content_dir, "plans")
        target_week_dir_name = f"week-{target_week_number:02d}"
        target_week_dir = os.path.join(plans_dir, target_week_dir_name)

        if os.path.exists(target_week_dir) and not force:
            logger.info(f"[PLAN GEN] Thư mục {target_week_dir_name} đã tồn tại. Dùng force=True để ghi đè.")
            return {
                "status": "already_exists",
                "message": f"Thư mục {target_week_dir_name} đã tồn tại.",
                "week_dir": target_week_dir
            }

        os.makedirs(target_week_dir, exist_ok=True)

        # 1. Bóc tách ngày tháng tuần mới (Bắt đầu Thứ 2 ngay sau Chủ Nhật tuần cũ, kết thúc Chủ Nhật)
        # Giả định tuần 1 kết thúc 18/10/2026 (Chủ Nhật)
        # Tuần 2: Thứ 2 (19/10/2026) -> Chủ Nhật (25/10/2026)
        # Tính toán linh hoạt dựa trên file tuần cũ nếu có
        start_date = date(2026, 10, 19)
        end_date = date(2026, 10, 25)

        prev_week_dir_name = f"week-{prev_week_number:02d}"
        prev_week_index_file = os.path.join(plans_dir, prev_week_dir_name, "index.md")
        if os.path.exists(prev_week_index_file):
            with open(prev_week_index_file, "r", encoding="utf-8") as f:
                prev_content = f.read()
            match = re.search(r"(\d{1,2})/(\d{1,2})\s*[-–]\s*(\d{1,2})/(\d{1,2})", prev_content)
            if match:
                p_end_d, p_end_m = int(match.group(3)), int(match.group(4))
                p_end_date = date(2026, p_end_m, p_end_d)
                # Bắt đầu vào Thứ 2 kế tiếp
                start_date = p_end_date + timedelta(days=1)
                # Kết thúc vào Chủ Nhật tuần đó (6 ngày sau Thứ 2)
                end_date = start_date + timedelta(days=6)

        start_str = start_date.strftime("%d/%m")
        end_str = end_date.strftime("%d/%m")
        year = start_date.year

        # 2. Đánh giá tuần cũ & Cập nhật Weekly Retrospective vào file tuần trước
        retrospective_data = self.evaluate_past_week(prev_week_number)
        if os.path.exists(prev_week_index_file):
            self._append_retrospective_to_prev_week(prev_week_index_file, retrospective_data, target_week_number)

        # 3. Lấy dữ liệu ảnh sách Cambridge 18 cho Test N (target_week_number)
        test_assets = self.get_cambridge_test_data(target_week_number)

        # 4. Tạo file index.md tuần mới
        created_files = []
        week_index_path = os.path.join(target_week_dir, "index.md")
        self._write_week_index(
            week_index_path,
            target_week_number,
            start_date,
            end_date,
            retrospective_data
        )
        created_files.append(os.path.relpath(week_index_path, self.content_dir))

        # 5. Tạo file test-2-listening.md
        listening_path = os.path.join(target_week_dir, f"test-{target_week_number}-listening.md")
        self._write_listening_note(
            listening_path,
            target_week_number,
            start_date,
            test_assets
        )
        created_files.append(os.path.relpath(listening_path, self.content_dir))

        # 6. Tạo file test-2-reading-p3.md (Passage 3)
        reading_date = start_date + timedelta(days=3)  # Thứ 5
        reading_path = os.path.join(target_week_dir, f"test-{target_week_number}-reading-p3.md")
        self._write_reading_note(
            reading_path,
            target_week_number,
            reading_date,
            test_assets
        )
        created_files.append(os.path.relpath(reading_path, self.content_dir))

        # 7. Tạo file test-2-writing.md
        writing_date = start_date + timedelta(days=4)  # Thứ 6
        writing_path = os.path.join(target_week_dir, f"test-{target_week_number}-writing.md")
        self._write_writing_note(
            writing_path,
            target_week_number,
            writing_date,
            test_assets
        )
        created_files.append(os.path.relpath(writing_path, self.content_dir))

        # 8. Tạo file vocab-week-XX.md
        vocab_path = os.path.join(target_week_dir, f"vocab-{target_week_dir_name}.md")
        self._write_vocab_note(
            vocab_path,
            target_week_number,
            start_date,
            end_date,
            test_assets
        )
        created_files.append(os.path.relpath(vocab_path, self.content_dir))

        # 9. Cập nhật liên kết cấp Macro tại content/plans/index.md và content/index.md
        self._update_macro_indexes(target_week_number, start_str, end_str, year)

        # 10. Kích hoạt Quartz HTML Rebuild tĩnh
        rebuild_quartz()

        return {
            "status": "success",
            "week_number": target_week_number,
            "date_range": f"{start_str} – {end_str}/{year}",
            "created_files": created_files,
            "retrospective_summary": retrospective_data.get("ai_retrospective_md", "")[:300] + "..."
        }

    def _append_retrospective_to_prev_week(
        self,
        file_path: str,
        retrospective_data: Dict[str, Any],
        next_week_num: int
    ):
        """Ghi nhận bản tổng kết tuần cũ vào cuối file index.md tuần trước"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            retro_section = f"""
---

## 📊 4. Đánh Giá & Tổng Kết Tuần Cũ (Weekly Retrospective)

> **Trạng thái:** Đã kết thúc trọn vẹn — Đã chuyển giao lịch trình sang [[plans/week-{next_week_num:02d}/|Kế Hoạch Tuần {next_week_num}]].  
> **Tổng số bài thi hoàn thành:** {retrospective_data['total_attempts']} bài  
> **Tổng số thẻ FSRS:** {retrospective_data['flashcards_total']} thẻ từ vựng  

{retrospective_data['ai_retrospective_md']}
"""
            # Nếu đã có mục 4 thì thay thế, nếu chưa thì append
            if "## 📊 4. Đánh Giá & Tổng Kết Tuần Cũ" in content:
                content = re.sub(r"## 📊 4\. Đánh Giá & Tổng Kết Tuần Cũ[\s\S]*", retro_section.lstrip(), content)
            else:
                content = content.rstrip() + "\n" + retro_section

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"[PLAN GEN] Đã cập nhật Retrospective vào file tuần trước: {file_path}")
        except Exception as e:
            logger.error(f"[PLAN GEN] Lỗi ghi Retrospective vào file cũ: {e}")

    def _write_week_index(
        self,
        file_path: str,
        week_num: int,
        start_date: date,
        end_date: date,
        retro_data: Dict[str, Any]
    ):
        start_str = start_date.strftime("%d/%m")
        end_str = end_date.strftime("%d/%m")
        year = start_date.year

        d1 = start_date
        d2 = start_date + timedelta(days=1)
        d3 = start_date + timedelta(days=2)
        d4 = start_date + timedelta(days=3)
        d5 = start_date + timedelta(days=4)
        d6 = start_date + timedelta(days=5)
        d7 = end_date

        content = f"""---
title: "[{start_str} - {end_str}] Kế Hoạch Tuần {week_num}"
aliases:
  - plans/week-{week_num:02d}
tags:
  - study-planner
  - week-{week_num:02d}
  - cambridge18
---

# 📅 Kế Hoạch Tuần {week_num}: {start_str} – {end_str}/{year} (Thích Ứng & Tăng Tốc)

> **Khung thời gian:** Thứ 2 ({d1.strftime('%d/%m/%Y')}) đến hết Chủ Nhật ({d7.strftime('%d/%m/%Y')})  
> **Nguyên tắc cốt lõi:** Cố định mỗi phiên ở mức **30 – 35 phút (Micro-sessions)** để tối ưu hóa tải trọng nhận thức (Cognitive Load Control).  
> **Quy tắc chu kỳ tuần:** Lịch trình tuần kết thúc trọn vẹn vào ngày **Chủ Nhật ({end_str})**, không kéo dài sang tuần sau.  
> **Trạng thái tuần:** Mới khởi tạo — Sẵn sàng học tập

---

## 🗓️ 1. Bảng Tổng Quan Lịch Trình Tuần {week_num} ({start_str} – {end_str})

| Ngày & Thứ | Kỹ Năng & Thời Lượng | Phương Pháp Thực Thi Trọng Tâm (Execution Focus) | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **Thứ 2**<br>_({d1.strftime('%d/%m/%Y')})_ | **Listening Core Test 2**<br>`35 phút` | • **30p:** Làm bài thi nghe tiêu chuẩn Cambridge 18 Test 2 (40 câu). Không dừng audio.<br>• **5p:** Gửi câu trả lời cho AI lưu trữ trung thực. 👉 **[[plans/week-{week_num:02d}/test-{week_num}-listening\\|Làm bài Test {week_num} Listening]]** | [ ] Sẵn sàng |
| **Thứ 3**<br>_({d2.strftime('%d/%m/%Y')})_ | **Reading Passage 1 & 2**<br>`35 phút` | • **20p:** Xử lý Reading Passage 1 (_Stonehenge_) & Passage 2 (_Living with AI_).<br>• **15p:** Đối chiếu bảng từ khóa và phân tích lỗi sai bẫy True/False/Not Given. | [ ] Sắp tới |
| **Thứ 4**<br>_({d3.strftime('%d/%m/%Y')})_ | **FSRS Vocab & Trap Drill**<br>`35 phút` | • **15p:** Ôn tập 100% thẻ từ vựng FSRS đến hạn.<br>• **20p:** Drill bẫy số ít/số nhiều và phát âm nối âm Listening Part 3. 👉 **[[plans/week-{week_num:02d}/vocab-week-{week_num:02d}\\|Mở Sổ Từ Vựng Tuần {week_num}]]** | [ ] Sắp tới |
| **Thứ 5**<br>_({d4.strftime('%d/%m/%Y')})_ | **Reading Keyword Mapping**<br>`35 phút` | • **20p:** Đọc hiểu chuyên sâu Reading Passage 3 (_Leonardo da Vinci's ideal city_).<br>• **15p:** Thực hành lập bảng Keyword Mapping đối chiếu từ vựng. 👉 **[[plans/week-{week_num:02d}/test-{week_num}-reading-p3\\|Làm bài Reading Passage 3]]** | [ ] Sắp tới |
| **Thứ 6**<br>_({d5.strftime('%d/%m/%Y')})_ | **Writing Task 1 & 2**<br>`35 phút` | • **15p:** Bóc tách biểu đồ Task 1 (Household income) & lập dàn ý Task 2.<br>• **20p:** Viết bài trên Split-Screen Workspace, nộp bài nhận phản hồi tiêu chí TR, CC, LR, GRA. 👉 **[[plans/week-{week_num:02d}/test-{week_num}-writing\\|Viết bài Writing Task 1 & 2]]** | [ ] Sắp tới |
| **Thứ 7**<br>_({d6.strftime('%d/%m/%Y')})_ | **Speaking Part 1 & 2**<br>`30 phút` | • **10p:** Lập dàn ý 1 phút chủ đề Examiner interview & Practical skills.<br>• **20p:** Thu âm 2 phút độc thoại liên tục, kiểm soát lỗi ngập ngừng (Fluency). | [ ] Sắp tới |
| **Chủ Nhật**<br>_({d7.strftime('%d/%m/%Y')})_ | **Core Review & Retrospective**<br>`35 phút` | • **15p:** Củng cố các thẻ từ vựng đánh giá Again/Hard trên FSRS.<br>• **20p:** AI tự động tổng kết tuần {week_num} và khởi tạo Kế Hoạch Tuần {week_num + 1}. | [ ] Sắp tới |

---

## 📝 2. Chi Tiết Nhiệm Vụ Hôm Nay: Thứ 2 ({d1.strftime('%d/%m/%Y')})

### 🎯 Listening Core Test 2 — 35 phút

- [ ] **30p:** Làm bài thi nghe tiêu chuẩn Cambridge 18 Test 2 (40 câu). Không dừng audio.
- [ ] **5p:** Gửi câu trả lời trực tiếp cho AI lưu trữ trung thực.
- [ ] **Đối soát:** Cung cấp đáp án chính thức để AI bóc tách bẫy âm thanh.
- 🔗 **Mở bài làm chi tiết:** 👉 [[plans/week-{week_num:02d}/test-{week_num}-listening|Làm bài Test {week_num} Listening]]
- 💡 **Nguyên tắc:** Mỗi phiên cố định 30–35 phút để đảm bảo Cognitive Load Control.

## 🔗 3. Mạng Lưới Kiến Thức Liên Quan

- 🎧 **Bài làm Listening:** [[plans/week-{week_num:02d}/test-{week_num}-listening|Test {week_num} Listening (Cam 18)]]
- 📖 **Bài làm Reading:** [[plans/week-{week_num:02d}/test-{week_num}-reading-p3|Test {week_num} Reading Passage 3 (Cam 18)]]
- ✍️ **Bài làm Writing:** [[plans/week-{week_num:02d}/test-{week_num}-writing|Test {week_num} Writing (Cam 18)]]
- 📚 **Sổ từ vựng trong tuần:** [[plans/week-{week_num:02d}/vocab-week-{week_num:02d}|Sổ Từ Vựng Trọng Tâm Tuần {week_num}]]
- 🎯 **Lộ trình tổng thể:** [[roadmap-5.0-to-7.5|Lộ trình 5.0 lên 7.5]]
- 🌐 **Tài nguyên học tập:** [[resources-learning-tools|Tổng Hợp Website & Công Cụ Luyện Thi IELTS]]
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_listening_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num

        # Trích xuất ảnh listening
        l_pages = test_assets.get("listening_pages", [])
        a_pages = test_assets.get("audioscript_pages", [])

        # Ghép ảnh theo Part
        part1_imgs = [p for p in l_pages if "Part 1" in p.get("title", "") or "Part 1" in p.get("phase_name", "")]
        part2_imgs = [p for p in l_pages if "Part 2" in p.get("title", "") or "Part 2" in p.get("phase_name", "")]
        part3_imgs = [p for p in l_pages if "Part 3" in p.get("title", "") or "Part 3" in p.get("phase_name", "")]
        part4_imgs = [p for p in l_pages if "Part 4" in p.get("title", "") or "Part 4" in p.get("phase_name", "")]

        def render_imgs(imgs):
            return "\n\n".join([f"![{img['title']} Trang {img['page_number']}]({img['url']})" for img in imgs if img.get("url")])

        # Bảng đối soát 40 câu
        rows_p1 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(1, 11)])
        rows_p2 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(11, 21)])
        rows_p3 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(21, 31)])
        rows_p4 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(31, 41)])

        audio_test_meta = self.get_test_audio_data(test_num)
        audio_parts = audio_test_meta.get("parts", {})

        def render_part_audio(p_num: int):
            p_data = audio_parts.get(str(p_num))
            if not p_data:
                return ""
            f_rel = f"../../{p_data['relative_path']}"
            return f"""<div class="ielts-audio-player-box" style="margin: 0.8rem 0 1rem 0; padding: 0.6rem 0.9rem; background: rgba(0, 113, 227, 0.05); border-radius: 10px; border: 1px solid rgba(0, 113, 227, 0.15);">
  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.35rem;">
    <span style="font-size: 0.8rem; font-weight: 700; color: #0071e3;">🎧 Audio {p_data.get('title', f'Part {p_num}')}</span>
    <span style="font-size: 0.72rem; color: #64748b; font-weight: 600;">{p_data.get('size_mb', '')} MB</span>
  </div>
  <audio controls preload="none" style="width: 100%; height: 36px; border-radius: 6px;">
    <source src="{f_rel}" type="audio/mpeg">
    Trình duyệt không hỗ trợ phát file âm thanh.
  </audio>
</div>"""

        content = f"""---
title: "[{day_str}] Test {test_num} Listening"
aliases:
  - test-cam18-test{test_num}-listening
tags:
  - listening
  - test-attempt
  - cambridge18
  - week-{week_num:02d}
---

# 🎧 Bài Làm: Cambridge 18 - Test {test_num} Listening

> **Tuần thực hiện:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num}]] — Phiên Hôm Nay: Thứ 2 ({day_date.strftime('%d/%m/%Y')})  
> **Tài liệu gốc:** Cambridge IELTS 18 Academic (Listening Test {test_num})  
> **Mục đích:** Bảng làm bài thi sạch sẽ, tích hợp nhập nhanh 40 câu, tính giờ và lưu trữ trung thực.

---

## 📑 Đề Thi & Lời Thoại (Hình Ảnh Trực Tiếp Từ Sách Gốc)

<details open>
<summary><b>📄 1. Đề Bài: Cambridge 18 - Test {test_num} Listening</b></summary>

### 🔹 Part 1: Questions 1 – 10

{render_part_audio(1)}

{render_imgs(part1_imgs) if part1_imgs else "_(Đang cập nhật hình ảnh)_"}

### 🔹 Part 2: Questions 11 – 20

{render_part_audio(2)}

{render_imgs(part2_imgs) if part2_imgs else "_(Đang cập nhật hình ảnh)_"}

### 🔹 Part 3: Questions 21 – 30

{render_part_audio(3)}

{render_imgs(part3_imgs) if part3_imgs else "_(Đang cập nhật hình ảnh)_"}

### 🔹 Part 4: Questions 31 – 40

{render_part_audio(4)}

{render_imgs(part4_imgs) if part4_imgs else "_(Đang cập nhật hình ảnh)_"}

</details>

<details>
<summary><b>📜 2. Audio Script: Lời Thoại Test {test_num} Listening - Mở sau khi làm bài</b></summary>

{render_imgs(a_pages) if a_pages else "_(Đang cập nhật audioscript)_"}

</details>

---

## 💡 Hướng Dẫn Nhập Liệu Nhanh (Shorthand Syntax)

Khi gửi bài làm cho AI để tự động tạo bảng đối soát, bạn có thể gõ nhanh theo cú pháp:

- **Làm đúng:** `3 dentist`, `12 a`, `24 c`
- **Làm sai (đối chiếu):** `1 dw137yz - dw307yz`, `4 car - parking / lý do: nghe nhầm danh từ`
- **Bỏ trống:** `16 - b / audio nói nhanh`

---

## 📋 Bảng Ghi Nhận Bài Làm Tương Tác (40 Câu)

<div class="ielts-sheet-card" data-sheet-id="cam18-test{test_num}-listening" data-start-q="1" data-end-q="40" data-timer="30">
  <div class="ielts-card-header">
    <div class="ielts-header-title">
      <span class="ielts-badge">Listening Test</span>
      <span class="ielts-target-pill">Cambridge 18 - Test {test_num} (40 Câu)</span>
    </div>
    <div class="ielts-timer-widget">
      <span class="ielts-timer-display">30:00</span>
      <div class="ielts-timer-controls">
        <button type="button" class="ielts-btn-timer ielts-btn-start" title="Bắt đầu tính giờ">▶️</button>
        <button type="button" class="ielts-btn-timer ielts-btn-pause" title="Tạm dừng" style="display:none;">⏸️</button>
        <button type="button" class="ielts-btn-timer ielts-btn-reset" title="Đặt lại đồng hồ">🔄</button>
      </div>
    </div>
  </div>

  <div class="ielts-stats-bar">
    <div class="ielts-stat-item">
      <span class="ielts-stat-label">Tiến độ:</span>
      <span class="ielts-stat-val ielts-sheet-progress">0 / 40 câu đã điền</span>
    </div>
    <div class="ielts-save-indicator">
      <span class="ielts-sheet-save-text">🟢 Tự động lưu LocalStorage</span>
    </div>
  </div>

  <div class="ielts-grid-answers"></div>

  <div class="ielts-card-actions">
    <button type="button" class="ielts-btn ielts-btn-primary ielts-btn-submit-ai">
      🚀 Gửi Câu Trả Lời Cho AI
    </button>
    <button type="button" class="ielts-btn ielts-btn-secondary ielts-btn-copy-shorthand">
      📋 Sao Chép Shorthand
    </button>
    <button type="button" class="ielts-btn ielts-btn-ghost ielts-btn-clear-sheet">
      🗑️ Xóa Bài Làm
    </button>
  </div>
  <div class="ielts-ai-response" style="display:none;"></div>
</div>

---

## 📊 Bảng Đối Soát Bài Làm

### 🔹 Part 1 (Questions 1 – 10)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p1}

### 🔹 Part 2 (Questions 11 – 20)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p2}

### 🔹 Part 3 (Questions 21 – 30)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p3}

### 🔹 Part 4 (Questions 31 – 40)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p4}

---

## 🔗 Mạng Lưới Kiến Thức Liên Quan

- 📅 **Kế hoạch cha:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num}]]
- 📚 **Sổ từ vựng tuần:** [[plans/week-{week_num:02d}/vocab-week-{week_num:02d}|Sổ Từ Vựng Trọng Tâm Tuần {week_num}]]
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_reading_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num

        r_pages = test_assets.get("reading_pages", [])
        # Lọc Passage 3 (thường là questions 27-40)
        p3_imgs = [p for p in r_pages if "Passage 3" in p.get("title", "") or "Passage 3" in p.get("phase_name", "") or p.get("page_number", 0) in [50, 51, 52, 53]]

        def render_imgs(imgs):
            return "\n\n".join([f"![{img['title']} Trang {img['page_number']}]({img['url']})" for img in imgs if img.get("url")])

        rows_reading = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(27, 41)])

        content = f"""---
title: "[{day_str}] Test {test_num} Reading P3"
aliases:
  - test-cam18-test{test_num}-reading-p3
tags:
  - reading
  - test-attempt
  - cambridge18
  - week-{week_num:02d}
---

# 📖 Bài Làm: Cambridge 18 - Test {test_num} Reading Passage 3

> **Tuần thực hiện:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num}]] — Phiên Hôm Nay: Thứ 5 ({day_date.strftime('%d/%m/%Y')})  
> **Tài liệu gốc:** Cambridge IELTS 18 Academic (Reading Test {test_num} Passage 3)  
> **Chủ đề bài đọc:** _Leonardo da Vinci's ideal city_ (Questions 27 – 40)

---

## 📑 Đề Thi Reading Passage 3 (Hình Ảnh Trực Tiếp Từ Sách Gốc)

<details open>
<summary><b>📄 Đề Bài Reading Passage 3 (Questions 27 – 40)</b></summary>

{render_imgs(p3_imgs) if p3_imgs else "_(Đang cập nhật hình ảnh đề bài)_"}

</details>

---

## 📋 Bảng Ghi Nhận Bài Làm Tương Tác (Questions 27 – 40)

<div class="ielts-sheet-card" data-sheet-id="cam18-test{test_num}-reading-p3" data-start-q="27" data-end-q="40" data-timer="20">
  <div class="ielts-card-header">
    <div class="ielts-header-title">
      <span class="ielts-badge">Reading Passage 3</span>
      <span class="ielts-target-pill">Cambridge 18 - Test {test_num} (14 Câu)</span>
    </div>
    <div class="ielts-timer-widget">
      <span class="ielts-timer-display">20:00</span>
      <div class="ielts-timer-controls">
        <button type="button" class="ielts-btn-timer ielts-btn-start" title="Bắt đầu tính giờ">▶️</button>
        <button type="button" class="ielts-btn-timer ielts-btn-pause" title="Tạm dừng" style="display:none;">⏸️</button>
        <button type="button" class="ielts-btn-timer ielts-btn-reset" title="Đặt lại đồng hồ">🔄</button>
      </div>
    </div>
  </div>

  <div class="ielts-stats-bar">
    <div class="ielts-stat-item">
      <span class="ielts-stat-label">Tiến độ:</span>
      <span class="ielts-stat-val ielts-sheet-progress">0 / 14 câu đã điền</span>
    </div>
    <div class="ielts-save-indicator">
      <span class="ielts-sheet-save-text">🟢 Tự động lưu LocalStorage</span>
    </div>
  </div>

  <div class="ielts-grid-answers"></div>

  <div class="ielts-card-actions">
    <button type="button" class="ielts-btn ielts-btn-primary ielts-btn-submit-ai">
      🚀 Gửi Câu Trả Lời Cho AI
    </button>
    <button type="button" class="ielts-btn ielts-btn-secondary ielts-btn-copy-shorthand">
      📋 Sao Chép Shorthand
    </button>
    <button type="button" class="ielts-btn ielts-btn-ghost ielts-btn-clear-sheet">
      🗑️ Xóa Bài Làm
    </button>
  </div>
  <div class="ielts-ai-response" style="display:none;"></div>
</div>

---

## 📊 Bảng Đối Soát Bài Làm (Questions 27 – 40)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_reading}

---

## 🔗 Mạng Lưới Kiến Thức Liên Quan

- 📅 **Kế hoạch cha:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num}]]
- 📚 **Sổ từ vựng tuần:** [[plans/week-{week_num:02d}/vocab-week-{week_num:02d}|Sổ Từ Vựng Trọng Tâm Tuần {week_num}]]
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_writing_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num

        w_pages = test_assets.get("writing_pages", [])
        t1_img = next((p["url"] for p in w_pages if "task_1" in p.get("title", "").lower() or p.get("page_number") == 54), "")
        t2_img = next((p["url"] for p in w_pages if "task_2" in p.get("title", "").lower() or p.get("page_number") == 55), "")

        content = f"""---
title: "[{day_str}] Test {test_num} Writing"
aliases:
  - test-cam18-test{test_num}-writing
tags:
  - writing
  - test-attempt
  - cambridge18
  - week-{week_num:02d}
---

# ✍️ Bài Làm: Cambridge 18 - Test {test_num} Writing

> **Tuần thực hiện:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num}]] — Phiên Hôm Nay: Thứ 6 ({day_date.strftime('%d/%m/%Y')})  
> **Tài liệu gốc:** Cambridge IELTS 18 Academic (Writing Test {test_num})  
> **Cấu trúc bài thi:** Task 1 (Báo cáo biểu đồ cột, ≥ 150 từ, 20 phút) & Task 2 (Nghị luận xã hội, ≥ 250 từ, 40 phút)

---

## 📑 Đề Thi Viết (Hình Ảnh Sách Gốc)

<details open>
<summary><b>📄 Đề Bài: Cambridge 18 - Test {test_num} Writing</b></summary>

### 🔹 Task 1: Bar Chart (Trang 54)

{f"![Writing Task 1 Trang 54]({t1_img})" if t1_img else "_(Hình ảnh Task 1 đang cập nhật)_"}

### 🔹 Task 2: Opinion Essay (Trang 55)

{f"![Writing Task 2 Trang 55]({t2_img})" if t2_img else "_(Hình ảnh Task 2 đang cập nhật)_"}

</details>

---

## 📊 Task 1: Báo Cáo Biểu Đồ Thu Nhập Hộ Gia Đình (Bar Chart)

### 📝 1. Khung Ghi Nhận Bài Viết Của Bạn (Task 1 Workspace)

<div class="ielts-writing-workspace" data-task-id="cam18-test{test_num}-w-task1" data-min-words="150" data-target-words="180">
  <div class="ielts-writing-header">
    <div class="ielts-writing-meta">
      <span class="ielts-badge">Writing Task 1</span>
      <span class="ielts-target-pill">Mục tiêu: 150 – 180 từ (20 phút)</span>
    </div>
    <div class="ielts-word-counter">
      <span class="ielts-word-count-num">0</span>
      <span class="ielts-word-count-label">từ</span>
    </div>
  </div>
  <textarea class="ielts-writing-textarea" placeholder="Gõ trực tiếp bài báo cáo Task 1 của bạn vào đây (Tự động lưu LocalStorage)..." rows="12"></textarea>
  <div class="ielts-writing-actions">
    <button type="button" class="ielts-btn ielts-btn-primary ielts-btn-submit-writing" data-task-type="task_1">
      🚀 Gửi Bài Task 1 Cho AI Chấm
    </button>
    <button type="button" class="ielts-btn ielts-btn-secondary ielts-btn-copy-writing">
      📋 Sao Chép
    </button>
  </div>
</div>

### 🔬 2. Phân Tích & Chẩn Đoán Chi Tiết Task 1 (Diagnostic Feedback)

#### 📝 Bài Làm Thực Tế Của Bạn (Lưu Trữ Nguyên Bản - 0 từ)

> _(Chưa có bài nộp. Hãy gõ bài làm vào khung phía trên và nhấn **"🚀 Gửi Bài Task 1 Cho AI Chấm"** để AI lưu trữ và chẩn đoán)._

#### ⚖️ Bảng Điểm 4 Tiêu Chí IELTS Chuyên Sâu

> _(Đang chờ nộp bài — Nhấn "🚀 Gửi Bài Task 1 Cho AI Chấm" để nhận bảng điểm 4 tiêu chí TR, CC, LR, GRA)._

---

## 💡 Task 2: Nghị Luận Xã Hội (Opinion Essay)

### 📝 1. Khung Ghi Nhận Bài Viết Của Bạn (Task 2 Workspace)

<div class="ielts-writing-workspace" data-task-id="cam18-test{test_num}-w-task2" data-min-words="250" data-target-words="280">
  <div class="ielts-writing-header">
    <div class="ielts-writing-meta">
      <span class="ielts-badge">Writing Task 2</span>
      <span class="ielts-target-pill">Mục tiêu: 250 – 280 từ (40 phút)</span>
    </div>
    <div class="ielts-word-counter">
      <span class="ielts-word-count-num">0</span>
      <span class="ielts-word-count-label">từ</span>
    </div>
  </div>
  <textarea class="ielts-writing-textarea" placeholder="Gõ trực tiếp bài luận Task 2 của bạn vào đây (Tự động lưu LocalStorage)..." rows="16"></textarea>
  <div class="ielts-writing-actions">
    <button type="button" class="ielts-btn ielts-btn-primary ielts-btn-submit-writing" data-task-type="task_2">
      🚀 Gửi Bài Task 2 Cho AI Chấm
    </button>
    <button type="button" class="ielts-btn ielts-btn-secondary ielts-btn-copy-writing">
      📋 Sao Chép
    </button>
  </div>
</div>

### 🔬 2. Phân Tích & Chẩn Đoán Chi Tiết Task 2 (Diagnostic Feedback)

#### 📝 Bài Làm Thực Tế Của Bạn (Lưu Trữ Nguyên Bản - 0 từ)

> _(Chưa có bài nộp. Hãy gõ bài làm vào khung phía trên và nhấn **"🚀 Gửi Bài Task 2 Cho AI Chấm"** để AI lưu trữ và chẩn đoán)._

#### ⚖️ Bảng Điểm 4 Tiêu Chí IELTS Chuyên Sâu

> _(Đang chờ nộp bài — Nhấn "🚀 Gửi Bài Task 2 Cho AI Chấm" để nhận bảng điểm 4 tiêu chí TR, CC, LR, GRA)._

---

## 🔗 Mạng Lưới Kiến Thức Liên Quan

- 📅 **Kế hoạch cha:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num}]]
- 📚 **Sổ từ vựng tuần:** [[plans/week-{week_num:02d}/vocab-week-{week_num:02d}|Sổ Từ Vựng Trọng Tâm Tuần {week_num}]]
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_vocab_note(
        self,
        file_path: str,
        week_num: int,
        start_date: date,
        end_date: date,
        test_assets: Dict[str, Any]
    ):
        start_str = start_date.strftime("%d/%m")
        end_str = end_date.strftime("%d/%m")
        sr_due_str = end_date.strftime("%Y-%m-%d")
        test_num = week_num

        # 20 từ vựng cốt lõi học thuật cho Test 2 (Milo's restaurant, Laki eruption, Leonardo's ideal city, household income)
        vocab_items = [
            ("pestilence", "noun", "/ˈpes.tɪ.ləns/", "Bệnh dịch hạch, dịch bệnh chết người", "After a pestilence that killed half the population in Milan, Leonardo turned to urban design.", "deadly pestilence, plague"),
            ("unconventional", "adj", "/ˌʌn.kənˈven.ʃən.əl/", "Khác thường, phá cách, không theo lối mòn", "His architectural designs were considered unconventional at the time.", "unconventional method, innovative"),
            ("sustainable", "adj", "/səˈsteɪ.nə.bəl/", "Bền vững, có thể duy trì lâu dài", "Unsustainable urban models are a key cause of global climate change.", "sustainable development, eco-friendly"),
            ("modernist", "adj/noun", "/ˈmɒd.ən.ɪst/", "Thuộc trường phái hiện đại", "The idea wasn't fully realized until the birth of the Modernist movement.", "modernist movement, architecture"),
            ("hydraulic", "adj", "/haɪˈdrɒl.ɪk/", "Thủy lực, liên quan đến sức nước", "Leonardo designed extensive hydraulic plants to create artificial canals.", "hydraulic system, power"),
            ("canal", "noun", "/kəˈnæl/", "Kênh đào nhân tạo", "The canals were supposed to make it easier for commercial boats to navigate inland.", "artificial canal, water channel"),
            ("navigate", "verb", "/ˈnæv.ɪ.ɡeɪt/", "Định hướng, di chuyển trên đường thủy/bộ", "Regulated by basins, the waterways helped boats navigate safely.", "navigate inland, navigate through"),
            ("adjacent", "adj", "/əˈdʒeɪ.sənt/", "Kế bên, liền kề", "The width of the streets ought to match the average height of adjacent houses.", "adjacent buildings, neighboring"),
            ("eruption", "noun", "/ɪˈrʌp.ʃən/", "Sự phun trào (núi lửa)", "The Laki volcanic eruption of 1783 caused widespread agricultural devastation.", "volcanic eruption, ash cloud"),
            ("devastation", "noun", "/ˌdev.əˈsteɪ.ʃən/", "Sự tàn phá, hủy diệt nặng nề", "The natural disaster brought immense economic and ecological devastation.", "cause devastation, disaster"),
            ("bracket", "noun", "/ˈbræk.ɪt/", "Khung phân loại, nhóm (thu nhập, tuổi)", "Households in the highest income bracket witnessed steady growth.", "income bracket, tax bracket"),
            ("disposable", "adj", "/dɪˈspəʊ.zə.bəl/", "Khả dụng (sau thuế), dùng một lần", "Rising disposable income contributed to increased consumer spending.", "disposable income, disposable products"),
            ("proportional", "adj", "/prəˈpɔː.ʃən.əl/", "Tương xứng, tỷ lệ thuận", "The expenditure was roughly proportional to household revenue.", "directly proportional, relative"),
            ("exponential", "adj", "/ˌek.spəˈnen.ʃəl/", "Theo cấp số nhân, tăng cực nhanh", "The tech sector experienced exponential expansion throughout the decade.", "exponential growth, surge"),
            ("counterpart", "noun", "/ˈkaʊn.tə.pɑːt/", "Đối tác, đối tượng tương đương", "Lower-income groups lagged behind their high-earning counterparts.", "international counterparts, peer"),
            ("rigorous", "adj", "/ˈrɪɡ.ər.əs/", "Nghiêm ngặt, chặt chẽ, chuẩn xác", "Urbanism emerged as a rigorous academic discipline during the Renaissance.", "rigorous testing, methodology"),
            ("specimen", "noun", "/ˈspes.ə.mɪn/", "Mẫu vật, tiêu bản khảo cứu", "Botanists collected numerous rare plant specimens from the rainforest.", "fossil specimen, lab sample"),
            ("scarcity", "noun", "/ˈskeə.sə.ti/", "Sự khan hiếm nguồn lực", "Severe water scarcity forced the council to introduce strict rationing.", "resource scarcity, acute shortage"),
            ("infrastructure", "noun", "/ˈɪn.frəˌstrʌk.tʃər/", "Cơ sở hạ tầng", "Modern cities require sustainable transportation and sanitation infrastructure.", "urban infrastructure, transport"),
            ("rehabilitate", "verb", "/ˌriː.həˈbɪl.ɪ.teɪt/", "Phục hồi, cải tạo lại", "The municipality allocated funds to rehabilitate historical town centers.", "rehabilitate buildings, restore")
        ]

        table_rows = []
        for word, pos, ipa, meaning, ex, syn in vocab_items:
            table_rows.append(f"| **{word}** | `{pos}` | `{ipa}` | {meaning} | _{ex}_ | {syn} |")

        table_body = "\n".join(table_rows)

        content = f"""---
title: "[{start_str} - {end_str}] Từ Vựng Tuần {week_num}"
aliases:
  - vocab-week-{week_num:02d}
tags:
  - vocab
  - week-{week_num:02d}
  - fsrs
  - cambridge18
sr-due: "{sr_due_str}"
---

# 📚 Sổ Từ Vựng Trọng Tâm Tuần {week_num} (Cambridge 18 - Test {test_num})

> **Tuần thực hiện:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num} ({start_str} – {end_str}/{start_date.year})]]  
> **Nguồn gốc:** Cambridge IELTS 18 Test {test_num} (Listening Parts 1–4, Reading Passages 1–3, Writing Tasks 1–2)  
> **Thuật toán ghi nhớ:** Tự động đồng bộ vào hệ thống Spaced Repetition FSRS v4 & Anki (`IELTS_Master_Deck.apkg`)

---

## 🗂️ Danh Mục Từ Vựng Học Thuật Cốt Lõi (20 Từ Mục Tiêu)

| Từ Vựng (Front) | Từ Loại | Phiên Âm (IPA) | Ý Nghĩa Tiếng Việt (Back) | Ví Dụ Ngữ Cảnh Trong Đề Thi | Collocations & Synonyms |
| :--- | :---: | :---: | :--- | :--- | :--- |
{table_body}

---

## 🔗 Mạng Lưới Kiến Thức Liên Quan

- 📅 **Kế hoạch cha:** [[plans/week-{week_num:02d}/|Kế Hoạch Tuần {week_num}]]
- 🎧 **Bài làm Listening:** [[plans/week-{week_num:02d}/test-{week_num}-listening|Test {week_num} Listening]]
- 📖 **Bài làm Reading:** [[plans/week-{week_num:02d}/test-{week_num}-reading-p3|Test {week_num} Reading P3]]
- ✍️ **Bài làm Writing:** [[plans/week-{week_num:02d}/test-{week_num}-writing|Test {week_num} Writing]]
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _update_macro_indexes(self, week_num: int, start_str: str, end_str: str, year: int):
        """Cập nhật liên kết tuần mới vào content/plans/index.md và content/index.md"""
        plans_index_path = os.path.join(self.content_dir, "plans", "index.md")
        root_index_path = os.path.join(self.content_dir, "index.md")

        new_plan_entry = (
            f"- [[plans/week-{week_num:02d}/|📅 Kế Hoạch Tuần {week_num}: {start_str} – {end_str}/{year}]] — "
            f"_Lịch trình tăng tốc Micro-sessions 30–35p: Listening Test {week_num}, Reading Passage 3 (Leonardo da Vinci), Writing Task 1 & 2, Speaking Routine._\n"
        )

        # 1. Update plans/index.md
        if os.path.exists(plans_index_path):
            with open(plans_index_path, "r", encoding="utf-8") as f:
                c = f.read()
            if f"week-{week_num:02d}" not in c:
                c = c.rstrip() + "\n" + new_plan_entry
                with open(plans_index_path, "w", encoding="utf-8") as f:
                    f.write(c)

        # 2. Update content/index.md
        if os.path.exists(root_index_path):
            with open(root_index_path, "r", encoding="utf-8") as f:
                rc = f.read()
            if f"week-{week_num:02d}" not in rc:
                # Chèn sau mục plans/week-01
                marker = "### 🗓️ Kế Hoạch Học Tập Theo Tuần (Weekly Study Plans)\n\n"
                if marker in rc:
                    parts = rc.split(marker)
                    new_rc = parts[0] + marker + new_plan_entry + parts[1]
                    with open(root_index_path, "w", encoding="utf-8") as f:
                        f.write(new_rc)

autonomous_plan_generator = AutonomousPlanGenerator()
