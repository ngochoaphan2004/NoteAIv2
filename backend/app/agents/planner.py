from typing import Dict, Any, List
from app.agents.state import AgentState

class PlanningAgent:
    def generate_plan(self, week_number: int, telemetry_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo kế hoạch học tập thích ứng (Adaptive Pacing) phân bổ thành các Micro-sessions 30-35 phút
        dựa trên telemetry lỗi sai và tiến độ FSRS.
        """
        target_score = "5.0 -> 7.5"
        
        sessions: List[Dict[str, Any]] = [
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

        return {
            "week": week_number,
            "target": target_score,
            "strategy": "Micro-sessions 30-35p thích ứng theo sai số thực tế",
            "micro_sessions": sessions,
            "checklist": [
                f"Đạt tỷ lệ nhớ lại (Retention Rate) >= 90% trên FSRS Tuần {week_number}",
                "Khắc phục triệt để bẫy số nhiều/số ít trong Listening Part 1",
                "Hoàn thành 1 bài viết Writing Task 1 không mắc lỗi chia bị động nội động từ"
            ]
        }

planner_agent = PlanningAgent()
