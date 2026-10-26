import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger("planner_agent")

class PlanningAgent:
    def generate_plan(self, week_number: int, telemetry_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Tạo kế hoạch học tập thích ứng (Adaptive Pacing) phân bổ thành các Micro-sessions 30-35 phút
        dựa trên telemetry lỗi sai và tiến độ FSRS. Sử dụng LLM Multi-Model Fallback khi có API Key.
        """
        target_score = "5.0 -> 7.5"

        # Nếu telemetry_summary chưa có và tuần > 1, tự động trích xuất từ Markdown SSOT & PostgreSQL
        if not telemetry_summary and week_number > 1:
            try:
                from app.services.plan_generator import autonomous_plan_generator
                past_eval = autonomous_plan_generator.evaluate_past_week(week_number - 1)
                telemetry_summary = {
                    "past_week": week_number - 1,
                    "completed_sessions": f"{past_eval.get('completed_sessions', 0)}/{past_eval.get('total_sessions', 7)}",
                    "accuracy_percent": f"{past_eval.get('accuracy_percent', 0)}%",
                    "trap_counts": past_eval.get("trap_counts", {}),
                    "flashcards_total": past_eval.get("flashcards_total", 0),
                    "attempts_summary": past_eval.get("attempts_summary", [])
                }
            except Exception as e:
                logger.warning(f"Không thể tự động trích xuất telemetry tuần cũ: {e}")
        
        # Lịch học Micro-sessions chuẩn mực mặc định
        default_sessions: List[Dict[str, Any]] = [
            {
                "session_id": 1,
                "duration_minutes": 35,
                "skill": "FSRS Vocabulary",
                "focus": f"Ôn tập từ vựng đến hạn (Tuần {week_number})",
                "activity": "Lật thẻ Flashcard trên SPA, củng cố các từ bị đánh giá Again/Hard."
            },
            {
                "session_id": 2,
                "duration_minutes": 30,
                "skill": "Listening Core Drill",
                "focus": "Luyện bẫy phát âm & ngữ âm học thuật",
                "activity": "Nghe chép chính tả 10 phút, đối chiếu bẫy số/chữ cái và quy tắc trọng âm -teen vs -ty."
            },
            {
                "session_id": 3,
                "duration_minutes": 35,
                "skill": "Reading Keyword Mapping",
                "focus": "Xây dựng bản đồ từ khóa Passage 3",
                "activity": "Lập bảng 3 cột: Câu hỏi ↔ Từ vựng bài đọc ↔ Từ đồng nghĩa (Synonyms) từ kho Qdrant."
            },
            {
                "session_id": 4,
                "duration_minutes": 35,
                "skill": "Writing Task 1 Repair Drill",
                "focus": "Chuẩn hóa tiêu chí GRA (Nội động từ & Mốc tương lai)",
                "activity": "Viết lại 5 câu biến động xu hướng không dùng bị động, viết đoạn Overview 2 câu chuẩn."
            }
        ]

        ai_advice: str = ""

        fallback_advice = (
            f"### 1. 🔍 Chẩn Đoán Điểm Nghẽn Nhận Thức\n\n"
            f"- **Phản xạ bẫy âm:** Vẫn còn tâm lý nghe đuổi theo từng từ vựng đơn lẻ thay vì định vị cấu trúc thông tin tổng thể.\n"
            f"- **Ngữ pháp & Hành văn:** Cần kiểm soát chặt chẽ các lỗi sơ đẳng như thì quá khứ đơn, sự hòa hợp chủ vị, và tuyệt đối không chia bị động cho nội động từ trong Writing Task 1.\n\n"
            f"### 2. ⏱️ Ma Trận Phân Bổ Micro-Sessions 30–35 Phút\n\n"
            f"- **Nguyên tắc 'Eat That Frog':** Đặt các phiên khó (Listening & Reading Passage 3) vào các ngày đầu tuần (Thứ 2 đến Thứ 4) khi năng lượng tập trung cao nhất.\n"
            f"- **Quy chuẩn 1 phiên 35p:** 5 phút kích hoạt từ khóa -> 20 phút làm bài tập trung cao độ -> 10 phút đối soát đáp án và nạp thẻ FSRS.\n\n"
            f"### 3. 🎯 Chiến Thuật Trị Bẫy Thực Chiến\n\n"
            f"- **Listening Part 1 & 2:** Áp dụng kỹ thuật Dictation phân biệt trọng âm số đuôi `-teen` và `-ty`, bắt bẫy chuyển hướng thông tin (distractors).\n"
            f"- **Reading Passage 3:** Lập bảng Keyword Mapping 3 cột (Từ khóa câu hỏi ↔ Từ vựng bài đọc ↔ Từ đồng nghĩa Synonyms) trước khi chốt đáp án.\n"
            f"- **Writing Task 1:** Thực hành viết lại 5 câu biến động xu hướng tăng/giảm hoàn toàn không dùng cấu trúc bị động sai quy tắc.\n\n"
            f"### 4. 📌 3 Quy Tắc Kỷ Luật Bất Biến Của Tuần\n\n"
            f"- **Đúng 35 phút dừng lại:** Khi hết thời gian phải dừng bút, chuyển sang đối soát để bảo vệ nhịp sinh học nhận thức.\n"
            f"- **Làm bài xong nạp thẻ ngay:** Mọi từ vựng mới hoặc câu làm sai phải được nạp vào FSRS trong vòng 5 phút sau khi nộp bài.\n"
            f"- **Duy trì kỷ luật 7 ngày:** Học ít nhưng liên tục mỗi ngày, tuyệt đối không để dồn bài tập sang cuối tuần."
        )

        # Nếu có API key, gọi LLM qua LLMService với cơ chế Multi-Model Fallback
        if settings.GEMINI_API_KEY or settings.OPENAI_API_KEY:
            try:
                system_message = (
                    "Bạn là Cố vấn Khảo thí & Chuyên gia Lập Kế Hoạch Học Tập IELTS NoteAI.v2 cấp cao.\n"
                    "Nhiệm vụ của bạn là chẩn đoán viễn trắc lỗi sai và xây dựng chiến lược học tập thích ứng (Adaptive Pacing) "
                    "cho từng tuần học theo triết lý Khoa học Nhận thức (Cognitive Load Control).\n\n"
                    "NGUYÊN TẮC QUẢN TRỊ TẢI TRỌNG NHẬN THỨC BẮT BUỘC:\n"
                    "1. Đơn nhiệm tuyệt đối: Mỗi phiên học chỉ kéo dài đúng 30–35 phút (Micro-session), nhắm thẳng vào 1 kỹ năng hoặc 1 dạng bẫy duy nhất.\n"
                    "2. Thực chứng dựa trên dữ liệu: Bám sát viễn trắc lỗi sai (telemetry), dạng bẫy thi thường gặp và tiến độ trí nhớ lặp ngắt quãng FSRS v4.\n"
                    "3. Định lượng và hành động rõ ràng: Hướng dẫn chính xác số phút, số câu, kỹ thuật cụ thể (Eat That Frog, Pomodoro 35p, Active Recall, Keyword Mapping), "
                    "tuyệt đối không đưa ra lời khuyên chung chung, mơ hồ hay lý thuyết sáo rỗng.\n"
                    "4. Văn phong sư phạm: Chuẩn mực, sắc sảo, truyền cảm hứng hành động và mang tính kỷ luật thép."
                )

                prompt = (
                    f"Dưới đây là hồ sơ năng lực và dữ liệu học tập thực tế của học viên:\n\n"
                    f"📊 BỐI CẢNH & VIỄN TRẮC HỌC TẬP:\n"
                    f"- Lộ trình mục tiêu: IELTS {target_score}\n"
                    f"- Tuần học kích hoạt: Tuần {week_number}\n"
                    f"- Viễn trắc tiến độ & bẫy lỗi sai gần đây: {telemetry_summary if telemetry_summary else 'Giai đoạn khởi động, chưa ghi nhận viễn trắc cũ; cần thiết lập kỷ luật và nhịp độ micro-sessions'}\n\n"
                    f"---\n\n"
                    f"NHIỆM VỤ: Hãy phân tích chuyên sâu dữ liệu trên và đưa ra bản HƯỚNG DẪN CHIẾN LƯỢC HỌC TẬP THÍCH ỨNG "
                    f"cho Tuần {week_number} theo cấu trúc Markdown 4 phần rõ ràng, rành mạch và chi tiết sau đây:\n\n"
                    f"### 1. 🔍 Chẩn Đoán Điểm Nghẽn Nhận Thức (Cognitive Bottlenecks)\n"
                    f"- Bóc tách chính xác 1–2 điểm nghẽn lớn nhất từ dữ liệu viễn trắc (ví dụ: bẫy âm số đếm -teen/-ty, bẫy distractor chuyển ý, lỗi chia thì/nội động từ Writing Task 1, hoặc tốc độ quét từ khóa Reading).\n"
                    f"- Phân tích nguyên nhân cốt lõi (tại sao học viên mắc lỗi: do phản xạ âm thanh, dịch thô trong đầu, hay quá tải thời gian làm bài).\n\n"
                    f"### 2. ⏱️ Ma Trận Phân Bổ Micro-Sessions 30–35 Phút (Session Allocation Blueprint)\n"
                    f"- Hướng dẫn cách phân bổ năng lượng trong tuần: phiên nào làm trước, phiên nào làm sau theo nguyên tắc 'Eat That Frog' (ưu tiên xử lý điểm yếu nhất vào đầu tuần khi năng lượng cao nhất).\n"
                    f"- Cấu trúc mẫu cho 1 phiên 35 phút chuẩn mực: 5–10p khởi động/ôn từ cũ -> 15–20p thực chiến/làm bài tập trung -> 5p đối soát & nạp từ vựng FSRS.\n\n"
                    f"### 3. 🎯 Chiến Thuật Trị Bẫy Thực Chiến (Targeted Drill Tactics)\n"
                    f"- Đưa ra 2–3 phương pháp luyện tập ngách, cụ thể cho tuần này (ví dụ: Dictation gạch chân âm đuôi cho Listening, Lập bảng Keyword Mapping 3 cột cho Reading, Drill viết lại câu không dùng bị động sai quy tắc cho Writing Task 1).\n\n"
                    f"### 4. 📌 3 Quy Tắc Kỷ Luật Bất Biến Của Tuần (Non-negotiable Execution Rules)\n"
                    f"- Đưa ra đúng 3 nguyên tắc hành động thép (mỗi nguyên tắc từ 15–25 từ, có gạch đầu dòng rõ ràng), đóng vai trò như kim chỉ nam giúp học viên duy trì chuỗi học tập mà không bị đứt đoạn hay quá tải."
                )

                ai_advice = llm_service.generate_text(prompt, system_message=system_message)
                logger.info(f"PlanningAgent: Đã tạo lời khuyên thích ứng qua model: {llm_service.last_used_model}")
            except Exception as e:
                logger.warning(f"PlanningAgent: Không thể gọi LLM ({e}), sử dụng chiến lược baseline mặc định.")

        return {
            "week": week_number,
            "target": target_score,
            "strategy": "Micro-sessions 30-35p thích ứng theo sai số thực tế",
            "micro_sessions": default_sessions,
            "ai_adaptive_advice": ai_advice if ai_advice else fallback_advice,
            "used_llm_model": llm_service.last_used_model,
            "checklist": [
                f"Đạt tỷ lệ nhớ lại (Retention Rate) >= 90% trên FSRS Tuần {week_number}",
                "Khắc phục triệt để bẫy số nhiều/số ít trong Listening Part 1",
                "Hoàn thành 1 bài viết Writing Task 1 không mắc lỗi chia bị động nội động từ"
            ]
        }

    def generate_full_week_markdown_package(self, week_number: int = 2, force: bool = False) -> Dict[str, Any]:
        """Tạo trọn gói thư mục tuần mới cùng các bài thi chi tiết và cập nhật Weekly Retrospective"""
        from app.services.plan_generator import autonomous_plan_generator
        return autonomous_plan_generator.generate_next_week(target_week_number=week_number, force=force)

planner_agent = PlanningAgent()

