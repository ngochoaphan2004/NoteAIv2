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
from app.services.template_service import template_service

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

        # 5. Tạo file test-N-listening-p1-p2.md (Thứ 2)
        l_p1_p2_path = os.path.join(target_week_dir, f"test-{target_week_number}-listening-p1-p2.md")
        self._write_listening_p1_p2_note(
            l_p1_p2_path,
            target_week_number,
            start_date,
            test_assets
        )
        created_files.append(os.path.relpath(l_p1_p2_path, self.content_dir))

        # 6. Tạo file test-N-listening-p3-p4.md (Thứ 3)
        l_p3_p4_date = start_date + timedelta(days=1)
        l_p3_p4_path = os.path.join(target_week_dir, f"test-{target_week_number}-listening-p3-p4.md")
        self._write_listening_p3_p4_note(
            l_p3_p4_path,
            target_week_number,
            l_p3_p4_date,
            test_assets
        )
        created_files.append(os.path.relpath(l_p3_p4_path, self.content_dir))

        # 7. Tạo file test-N-reading-p1-p2.md (Thứ 4)
        r_p1_p2_date = start_date + timedelta(days=2)
        r_p1_p2_path = os.path.join(target_week_dir, f"test-{target_week_number}-reading-p1-p2.md")
        self._write_reading_p1_p2_note(
            r_p1_p2_path,
            target_week_number,
            r_p1_p2_date,
            test_assets
        )
        created_files.append(os.path.relpath(r_p1_p2_path, self.content_dir))

        # 8. Tạo file test-N-reading-p3.md (Thứ 5)
        reading_date = start_date + timedelta(days=3)  # Thứ 5
        reading_path = os.path.join(target_week_dir, f"test-{target_week_number}-reading-p3.md")
        self._write_reading_p3_note(
            reading_path,
            target_week_number,
            reading_date,
            test_assets
        )
        created_files.append(os.path.relpath(reading_path, self.content_dir))

        # 9. Tạo file test-N-writing.md (Thứ 6)
        writing_date = start_date + timedelta(days=4)  # Thứ 6
        writing_path = os.path.join(target_week_dir, f"test-{target_week_number}-writing.md")
        self._write_writing_note(
            writing_path,
            target_week_number,
            writing_date,
            test_assets
        )
        created_files.append(os.path.relpath(writing_path, self.content_dir))

        # 10. Tạo file test-N-speaking.md (Thứ 7)
        speaking_date = start_date + timedelta(days=5)  # Thứ 7
        speaking_path = os.path.join(target_week_dir, f"test-{target_week_number}-speaking.md")
        self._write_speaking_note(
            speaking_path,
            target_week_number,
            speaking_date,
            test_assets
        )
        created_files.append(os.path.relpath(speaking_path, self.content_dir))

        # 11. Tạo file review-week-XX.md (Chủ Nhật)
        review_path = os.path.join(target_week_dir, f"review-{target_week_dir_name}.md")
        self._write_review_note(
            review_path,
            target_week_number,
            end_date
        )
        created_files.append(os.path.relpath(review_path, self.content_dir))

        # 12. Tạo file vocab-week-XX.md
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

        week_padded = f"{week_num:02d}"
        context = {
            "START_DD_MM": start_str,
            "END_DD_MM": end_str,
            "WEEK_NUM": str(week_num),
            "WEEK_PADDED": week_padded,
            "SOURCE_TAG": "cambridge18",
            "START_DATE": f"{start_str}/{year}",
            "END_DATE": f"{end_str}/{year}",
            "THEME_TITLE": "Thích Ứng & Chia Nhỏ Bài Học",
            "SUNDAY_DATE": end_str,
            "WEEK_STATUS": "Mới khởi tạo — Sẵn sàng học tập",
            "TEST_NUM": str(week_num),
            "DATE_MON": d1.strftime('%d/%m/%Y'),
            "DATE_TUE": d2.strftime('%d/%m/%Y'),
            "DATE_WED": d3.strftime('%d/%m/%Y'),
            "DATE_THU": d4.strftime('%d/%m/%Y'),
            "DATE_FRI": d5.strftime('%d/%m/%Y'),
            "DATE_SAT": d6.strftime('%d/%m/%Y'),
            "DATE_SUN": d7.strftime('%d/%m/%Y'),
            "STATUS_MON": "[ ] Sẵn sàng",
            "STATUS_TUE": "[ ] Sắp tới",
            "STATUS_WED": "[ ] Sắp tới",
            "STATUS_THU": "[ ] Sắp tới",
            "STATUS_FRI": "[ ] Sắp tới",
            "STATUS_SAT": "[ ] Sắp tới",
            "STATUS_SUN": "[ ] Sắp tới",
            "TODAY_FULL_NAME": f"Thứ 2 ({d1.strftime('%d/%m/%Y')})",
            "TODAY_SKILL": "Listening Part 1 & 2",
            "TODAY_DURATION": "35 phút",
            "TODAY_FOCUS": f"• **15p (Part 1):** Nghe và làm 10 câu đầu Cambridge 18 Test {week_num}. Bắt bẫy số và ngày tháng.<br>• **15p (Part 2):** Nghe và làm câu 11 – 20. Đánh dấu từ khóa trước khi nghe.",
            "TODAY_TARGET_FILE": f"test-{week_num}-listening-p1-p2",
            "TODAY_TARGET_NAME": f"Test {week_num} Listening P1-P2"
        }

        content = template_service.render("weekly_plan", context)
        val = template_service.validate_markdown(content, "weekly_plan")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template weekly_plan: {val['errors']}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_listening_p1_p2_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num
        week_padded = f"{week_num:02d}"

        l_pages = test_assets.get("listening_pages", [])
        part1_imgs = [p for p in l_pages if "Part 1" in p.get("title", "") or "Part 1" in p.get("phase_name", "")]
        part2_imgs = [p for p in l_pages if "Part 2" in p.get("title", "") or "Part 2" in p.get("phase_name", "")]

        def render_imgs(imgs):
            return "\n\n".join([f"![{img['title']} Trang {img['page_number']}]({img['url']})" for img in imgs if img.get("url")])

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

        audio_and_image_blocks = f"""### 🔹 Part 1: Questions 1 – 10

{render_part_audio(1)}

{render_imgs(part1_imgs) if part1_imgs else "_(Đang cập nhật hình ảnh đề bài Part 1)_"}

---

### 🔹 Part 2: Questions 11 – 20

{render_part_audio(2)}

{render_imgs(part2_imgs) if part2_imgs else "_(Đang cập nhật hình ảnh đề bài Part 2)_"}"""

        rows_p1 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(1, 11)])
        rows_p2 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(11, 21)])

        verification_tables = f"""### 🔹 Part 1 (Questions 1 – 10)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p1}

---

### 🔹 Part 2 (Questions 11 – 20)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p2}"""

        context = {
            "DATE_DD_MM": day_str,
            "TEST_NUM": str(test_num),
            "PART_LABEL_SHORT": "P1-P2",
            "SOURCE_SLUG": "cam18",
            "PART_SLUG": "p1-p2",
            "SOURCE_TAG": "cambridge18",
            "PART_TAG_1": "part-1",
            "PART_TAG_2": "part-2",
            "WEEK_PADDED": week_padded,
            "SOURCE_NAME": "Cambridge 18",
            "PART_LABEL_FULL": "Part 1 & Part 2",
            "WEEK_NUM": str(week_num),
            "START_DD_MM": day_str,
            "END_DD_MM": (day_date + timedelta(days=6)).strftime("%d/%m"),
            "DAY_NAME": f"Thứ 2 ({day_date.strftime('%d/%m/%Y')})",
            "TEST_TIMER": "18",
            "REVIEW_TIMER": "17",
            "AUDIO_AND_IMAGE_BLOCKS": audio_and_image_blocks,
            "SHEET_ID": f"cam18-test{test_num}-listening-p1-p2",
            "START_Q": "1",
            "END_Q": "20",
            "TOTAL_QUESTIONS": "20",
            "VERIFICATION_TABLES": verification_tables,
            "NEXT_PART_FILE": f"test-{test_num}-listening-p3-p4",
            "NEXT_PART_TITLE": f"Test {test_num} Listening P3-P4"
        }

        content = template_service.render("listening_session", context)
        val = template_service.validate_markdown(content, "listening_session")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template listening_p1_p2: {val['errors']}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_listening_p3_p4_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num
        week_padded = f"{week_num:02d}"

        l_pages = test_assets.get("listening_pages", [])
        part3_imgs = [p for p in l_pages if "Part 3" in p.get("title", "") or "Part 3" in p.get("phase_name", "")]
        part4_imgs = [p for p in l_pages if "Part 4" in p.get("title", "") or "Part 4" in p.get("phase_name", "")]

        def render_imgs(imgs):
            return "\n\n".join([f"![{img['title']} Trang {img['page_number']}]({img['url']})" for img in imgs if img.get("url")])

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

        audio_and_image_blocks = f"""### 🔹 Part 3: Questions 21 – 30

{render_part_audio(3)}

{render_imgs(part3_imgs) if part3_imgs else "_(Đang cập nhật hình ảnh đề bài Part 3)_"}

---

### 🔹 Part 4: Questions 31 – 40

{render_part_audio(4)}

{render_imgs(part4_imgs) if part4_imgs else "_(Đang cập nhật hình ảnh đề bài Part 4)_"}"""

        rows_p3 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(21, 31)])
        rows_p4 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(31, 41)])

        verification_tables = f"""### 🔹 Part 3 (Questions 21 – 30)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p3}

---

### 🔹 Part 4 (Questions 31 – 40)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p4}"""

        context = {
            "DATE_DD_MM": day_str,
            "TEST_NUM": str(test_num),
            "PART_LABEL_SHORT": "P3-P4",
            "SOURCE_SLUG": "cam18",
            "PART_SLUG": "p3-p4",
            "SOURCE_TAG": "cambridge18",
            "PART_TAG_1": "part-3",
            "PART_TAG_2": "part-4",
            "WEEK_PADDED": week_padded,
            "SOURCE_NAME": "Cambridge 18",
            "PART_LABEL_FULL": "Part 3 & Part 4",
            "WEEK_NUM": str(week_num),
            "START_DD_MM": (day_date - timedelta(days=1)).strftime("%d/%m"),
            "END_DD_MM": (day_date + timedelta(days=5)).strftime("%d/%m"),
            "DAY_NAME": f"Thứ 3 ({day_date.strftime('%d/%m/%Y')})",
            "TEST_TIMER": "18",
            "REVIEW_TIMER": "17",
            "AUDIO_AND_IMAGE_BLOCKS": audio_and_image_blocks,
            "SHEET_ID": f"cam18-test{test_num}-listening-p3-p4",
            "START_Q": "21",
            "END_Q": "40",
            "TOTAL_QUESTIONS": "20",
            "VERIFICATION_TABLES": verification_tables,
            "NEXT_PART_FILE": f"test-{test_num}-reading-p1-p2",
            "NEXT_PART_TITLE": f"Test {test_num} Reading P1-P2"
        }

        content = template_service.render("listening_session", context)
        val = template_service.validate_markdown(content, "listening_session")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template listening_p3_p4: {val['errors']}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_reading_p1_p2_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num
        week_padded = f"{week_num:02d}"

        r_pages = test_assets.get("reading_pages", [])
        p1_imgs = [p for p in r_pages if "Passage 1" in p.get("title", "") or "Passage 1" in p.get("phase_name", "")]
        p2_imgs = [p for p in r_pages if "Passage 2" in p.get("title", "") or "Passage 2" in p.get("phase_name", "")]

        def render_imgs(imgs):
            return "\n\n".join([f"![{img['title']} Trang {img['page_number']}]({img['url']})" for img in imgs if img.get("url")])

        prompt_image_blocks = f"""### 🔹 Passage 1: Questions 1 – 13

{render_imgs(p1_imgs) if p1_imgs else "_(Đang cập nhật hình ảnh đề bài Passage 1)_"}

---

### 🔹 Passage 2: Questions 14 – 26

{render_imgs(p2_imgs) if p2_imgs else "_(Đang cập nhật hình ảnh đề bài Passage 2)_"}"""

        rows_p1 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(1, 14)])
        rows_p2 = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(14, 27)])

        verification_tables = f"""### 🔹 Passage 1 (Questions 1 – 13)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p1}

---

### 🔹 Passage 2 (Questions 14 – 26)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_p2}"""

        context = {
            "DATE_DD_MM": day_str,
            "TEST_NUM": str(test_num),
            "PART_LABEL_SHORT": "P1-P2",
            "SOURCE_SLUG": "cam18",
            "PART_SLUG": "p1-p2",
            "SOURCE_TAG": "cambridge18",
            "PASSAGE_TAG_1": "passage-1",
            "PASSAGE_TAG_2": "passage-2",
            "WEEK_PADDED": week_padded,
            "SOURCE_NAME": "Cambridge 18",
            "PASSAGE_LABEL_FULL": "Passage 1 & Passage 2",
            "WEEK_NUM": str(week_num),
            "START_DD_MM": (day_date - timedelta(days=2)).strftime("%d/%m"),
            "END_DD_MM": (day_date + timedelta(days=4)).strftime("%d/%m"),
            "DAY_NAME": f"Thứ 4 ({day_date.strftime('%d/%m/%Y')})",
            "READ_TIMER": "25",
            "REVIEW_TIMER": "10",
            "PROMPT_IMAGE_BLOCKS": prompt_image_blocks,
            "SHEET_ID": f"cam18-test{test_num}-reading-p1-p2",
            "START_Q": "1",
            "END_Q": "26",
            "TOTAL_QUESTIONS": "26",
            "VERIFICATION_TABLES": verification_tables,
            "NEXT_PART_FILE": f"test-{test_num}-reading-p3",
            "NEXT_PART_TITLE": f"Test {test_num} Reading P3"
        }

        content = template_service.render("reading_session", context)
        val = template_service.validate_markdown(content, "reading_session")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template reading_p1_p2: {val['errors']}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_reading_p3_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num
        week_padded = f"{week_num:02d}"

        r_pages = test_assets.get("reading_pages", [])
        p3_imgs = [p for p in r_pages if "Passage 3" in p.get("title", "") or "Passage 3" in p.get("phase_name", "")]

        def render_imgs(imgs):
            return "\n\n".join([f"![{img['title']} Trang {img['page_number']}]({img['url']})" for img in imgs if img.get("url")])

        prompt_image_blocks = render_imgs(p3_imgs) if p3_imgs else "_(Đang cập nhật hình ảnh đề bài Passage 3)_"

        rows_reading = "\n".join([f"| **{i}** | `[ ]` | | ⚪ | |" for i in range(27, 41)])

        verification_tables = f"""### 🔹 Passage 3 (Questions 27 – 40)

| STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú Lỗi Sai / Phân Tích Bẫy |
| :---: | :--- | :--- | :---: | :--- |
{rows_reading}"""

        context = {
            "DATE_DD_MM": day_str,
            "TEST_NUM": str(test_num),
            "PART_LABEL_SHORT": "P3",
            "SOURCE_SLUG": "cam18",
            "PART_SLUG": "p3",
            "SOURCE_TAG": "cambridge18",
            "PASSAGE_TAG_1": "passage-3",
            "PASSAGE_TAG_2": "academic",
            "WEEK_PADDED": week_padded,
            "SOURCE_NAME": "Cambridge 18",
            "PASSAGE_LABEL_FULL": "Passage 3",
            "WEEK_NUM": str(week_num),
            "START_DD_MM": (day_date - timedelta(days=3)).strftime("%d/%m"),
            "END_DD_MM": (day_date + timedelta(days=3)).strftime("%d/%m"),
            "DAY_NAME": f"Thứ 5 ({day_date.strftime('%d/%m/%Y')})",
            "READ_TIMER": "20",
            "REVIEW_TIMER": "15",
            "PROMPT_IMAGE_BLOCKS": prompt_image_blocks,
            "SHEET_ID": f"cam18-test{test_num}-reading-p3",
            "START_Q": "27",
            "END_Q": "40",
            "TOTAL_QUESTIONS": "14",
            "VERIFICATION_TABLES": verification_tables,
            "NEXT_PART_FILE": f"test-{test_num}-writing",
            "NEXT_PART_TITLE": f"Test {test_num} Writing Task 1"
        }

        content = template_service.render("reading_session", context)
        val = template_service.validate_markdown(content, "reading_session")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template reading_p3: {val['errors']}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_speaking_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date,
        test_assets: Dict[str, Any]
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num
        week_padded = f"{week_num:02d}"

        s_pages = test_assets.get("speaking_pages", [])
        s_img = s_pages[0].get("url") if s_pages else ""
        s_page_num = s_pages[0].get("page_number", "") if s_pages else ""
        s_topic = s_pages[0].get("topic", "Examiner interview & Practical skills") if s_pages else "Practical skills"

        cue_card_content = f"""    <p><b>Topic: {s_topic}</b></p>
    <p>You should say:</p>
    <ul>
      <li>What the challenge / situation was</li>
      <li>When and where it happened</li>
      <li>What you did to solve it</li>
    </ul>
    <p>and explain how you felt after solving this challenge.</p>"""

        context = {
            "DATE_DD_MM": day_str,
            "TEST_NUM": str(test_num),
            "PART_LABEL_SHORT": "Part 2",
            "SOURCE_SLUG": "cam18",
            "PART_NUM": "2",
            "SOURCE_TAG": "cambridge18",
            "WEEK_PADDED": week_padded,
            "SOURCE_NAME": "Cambridge 18",
            "PART_LABEL_FULL": "Part 2",
            "WEEK_NUM": str(week_num),
            "START_DD_MM": (day_date - timedelta(days=5)).strftime("%d/%m"),
            "END_DD_MM": (day_date + timedelta(days=1)).strftime("%d/%m"),
            "DAY_NAME": f"Thứ 7 ({day_date.strftime('%d/%m/%Y')})",
            "PAGE_STR": f"Trang {s_page_num}" if s_page_num else "",
            "TOTAL_TIMER": "30",
            "PREPARE_TIMER": "10",
            "SPEAK_TIMER": "2",
            "SPEAK_TIMER_DISPLAY": "02:00",
            "CUE_CARD_CONTENT": cue_card_content,
            "PROMPT_IMAGE_BLOCKS": f"![Speaking Test {test_num} Trang {s_page_num}]({s_img})" if s_img else "_(Hình ảnh đề thi Speaking đang cập nhật)_",
            "OUTLINE_WHAT": "_Ví dụ: Project deadline, unexpected situation, university / workplace_",
            "OUTLINE_WHEN": "_Ví dụ: Last semester / about two years ago_",
            "OUTLINE_HOW": "_Ví dụ: Formulated plan, consulted supervisor, prioritized tasks_",
            "OUTLINE_WHY": "_Ví dụ: Resolved successfully, immense relief, learned valuable lesson_",
            "NEXT_PART_FILE": f"review-week-{week_padded}",
            "NEXT_PART_TITLE": f"Phiên Ôn Tập & Tổng Kết Tuần {week_num}"
        }

        content = template_service.render("speaking_session", context)
        val = template_service.validate_markdown(content, "speaking_session")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template speaking_session: {val['errors']}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _write_review_note(
        self,
        file_path: str,
        test_num: int,
        day_date: date
    ):
        day_str = day_date.strftime("%d/%m")
        week_num = test_num
        week_padded = f"{week_num:02d}"

        context = {
            "DATE_DD_MM": day_str,
            "WEEK_NUM": str(week_num),
            "WEEK_PADDED": week_padded,
            "SOURCE_TAG": "cambridge18",
            "SOURCE_NAME": f"Cambridge 18 - Test {test_num}",
            "START_DD_MM": (day_date - timedelta(days=6)).strftime("%d/%m"),
            "END_DD_MM": day_str
        }

        content = template_service.render("review_week", context)
        val = template_service.validate_markdown(content, "review_week")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template review_week: {val['errors']}")

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
        week_padded = f"{week_num:02d}"

        w_pages = test_assets.get("writing_pages", [])
        t1_img = next((p["url"] for p in w_pages if "task_1" in p.get("title", "").lower() or p.get("page_number") == 54), "")
        
        prompt_image_blocks = f"![Writing Task 1 Trang 54]({t1_img})" if t1_img else "_(Hình ảnh Task 1 đang cập nhật)_"
        outline_steps = """1. **Phân tích biểu đồ (3 phút):** Xác định dạng bài (Biểu đồ cột có xu hướng theo thời gian hay so sánh tĩnh), thì động từ và đơn vị đo lường.
2. **Viết Introduction & Overview (5 phút):** Paraphrase đề bài trong 1 câu; chỉ ra 2 đặc điểm nổi bật nhất (xu hướng tăng giảm mạnh nhất hoặc nhóm cao nhất).
3. **Phát triển 2 đoạn Thân bài (12 phút):** Gom nhóm số liệu theo năm hoặc theo hạng mục; sử dụng cấu trúc so sánh tương phản linh hoạt (`While...`, `In contrast...`)."""

        context = {
            "DATE_DD_MM": day_str,
            "TEST_NUM": str(test_num),
            "TASK_NUM": "1",
            "SOURCE_SLUG": "cam18",
            "SOURCE_TAG": "cambridge18",
            "WEEK_PADDED": week_padded,
            "SOURCE_NAME": "Cambridge 18",
            "WEEK_NUM": str(week_num),
            "START_DD_MM": (day_date - timedelta(days=4)).strftime("%d/%m"),
            "END_DD_MM": (day_date + timedelta(days=2)).strftime("%d/%m"),
            "DAY_NAME": f"Thứ 6 ({day_date.strftime('%d/%m/%Y')})",
            "PAGE_STR": "Trang 54",
            "PREPARE_TIMER": "15",
            "WRITE_TIMER": "20",
            "TARGET_WORDS": "150",
            "TASK_TOPIC": "Bar Chart (Thu Nhập Hộ Gia Đình)",
            "PROMPT_IMAGE_BLOCKS": prompt_image_blocks,
            "OUTLINE_STEPS": outline_steps,
            "NEXT_PART_FILE": f"test-{test_num}-speaking",
            "NEXT_PART_TITLE": f"Test {test_num} Speaking Part 2"
        }

        content = template_service.render("writing_session", context)
        val = template_service.validate_markdown(content, "writing_session")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template writing_session: {val['errors']}")

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

        context = {
            "START_DD_MM": start_str,
            "END_DD_MM": end_str,
            "WEEK_NUM": str(week_num),
            "WEEK_PADDED": f"{week_num:02d}",
            "SOURCE_SLUG": "cam18",
            "SOURCE_TAG": "cambridge18",
            "SR_DUE_DATE": sr_due_str,
            "SOURCE_NAME": f"Cambridge 18 - Test {test_num}",
            "SOURCE_COVERAGE": "Test 2: Listening P1–P4, Reading P1–P3, Writing Task 1",
            "TOTAL_WORDS": str(len(vocab_items)),
            "VOCAB_ROWS": table_body
        }

        content = template_service.render("vocab_week", context)
        val = template_service.validate_markdown(content, "vocab_week")
        if not val["valid"]:
            logger.error(f"[PLAN GEN] Lỗi validation template vocab_week: {val['errors']}")

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
