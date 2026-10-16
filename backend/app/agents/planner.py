import logging
from typing import Dict, Any, List
from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger("planner_agent")

class PlanningAgent:
    def generate_plan(self, week_number: int, telemetry_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo kế hoạch học tập thích ứng (Adaptive Pacing) phân bổ thành các Micro-sessions 30-35 phút
        dựa trên telemetry lỗi sai và tiến độ FSRS. Sử dụng LLM Multi-Model Fallback khi có API Key.
        """
        target_score = "5.0 -> 7.5"
        
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

        # Nếu có API key, gọi LLM qua LLMService với cơ chế Multi-Model Fallback
        if settings.GEMINI_API_KEY or settings.OPENAI_API_KEY:
            try:
                prompt = (
                    f"Người học đang ở lộ trình IELTS {target_score}, bắt đầu Tuần {week_number}. "
                    f"Thông tin lỗi sai và viễn trắc gần đây: {telemetry_summary}. "
                    f"Hãy đưa ra 3 lời khuyên ngắn gọn (mỗi câu tối đa 20 từ) về cách phân bổ "
                    f"các Micro-sessions 30-35 phút để đạt hiệu quả cao nhất mà không bị quá tải."
                )
                system_message = (
                    "Bạn là Chuyên gia Lập Kế Hoạch Luyện Thi IELTS NoteAI.v2 theo triết lý Cognitive Load Control. "
                    "Trả lời súc tích, cụ thể, bằng tiếng Việt."
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
            "ai_adaptive_advice": ai_advice if ai_advice else "Tập trung hoàn thành 100% các phiên 30-35 phút đơn nhiệm để duy trì đà học liên tục.",
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

