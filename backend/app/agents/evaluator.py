import logging
from typing import List, Optional
from app.agents.state import AgentState, EvaluationOutput, QuestionResult
from app.services.markdown_parser import markdown_parser
from app.services.rag_engine import rag_engine
from app.core.config import settings

logger = logging.getLogger("evaluator_agent")

class EvaluatorAgent:
    def evaluate(self, state: AgentState) -> AgentState:
        """
        Đánh giá bài làm của người học tuân thủ nghiêm ngặt NGUYÊN TẮC VÀNG:
        - KHÔNG tự đoán đáp án đúng/sai nếu người học chưa cung cấp bảng key.
        - Chỉ ghi nhận trung thực đáp án thực tế của người học.
        """
        raw_text = state.input_text
        parsed_items = markdown_parser.parse_test_shorthand(raw_text)

        if not parsed_items:
            state.error = "Không tìm thấy câu trả lời nào theo cú pháp hợp lệ."
            return state

        # Kiểm tra xem người học có cung cấp đáp án đối chiếu không
        has_any_key = any(item.get("correct_answer") is not None for item in parsed_items)
        state.has_official_key = has_any_key

        questions: List[QuestionResult] = []
        correct_count = 0
        total_graded = 0

        for item in parsed_items:
            q_num = item["question_number"]
            user_ans = item["user_answer"]
            correct_ans = item.get("correct_answer")
            is_corr = item.get("is_correct")
            trap = item.get("trap_type")
            exp = item.get("explanation")

            if has_any_key and correct_ans is not None:
                # Đối chiếu khi có key
                total_graded += 1
                if user_ans.strip().lower() == correct_ans.strip().lower():
                    is_corr = True
                    correct_count += 1
                else:
                    is_corr = False
            else:
                # TUYỆT ĐỐI KHÔNG SUY ĐOÁN KHI THIẾU KEY
                is_corr = None
                correct_ans = None

            questions.append(QuestionResult(
                question_number=q_num,
                user_answer=user_ans,
                correct_answer=correct_ans,
                is_correct=is_corr,
                trap_type=trap,
                explanation=exp
            ))

        # Tính toán phân số điểm & Band Score (CHỈ KHI CÓ ĐÁP ÁN CHÍNH THỨC)
        score_fraction: Optional[str] = None
        band_score: Optional[float] = None
        strengths: List[str] = []
        weaknesses: List[str] = []
        drills: List[str] = []

        if has_any_key and total_graded > 0:
            score_fraction = f"{correct_count}/{len(questions)}"
            band_score = self._estimate_band_score(correct_count, len(questions), state.skill)
            strengths.append(f"Hoàn thành đối soát {total_graded} câu hỏi trong bài.")
            if correct_count < len(questions):
                weaknesses.append("Một số câu mắc bẫy ngữ âm hoặc chuyển ý trong audio.")
                drills.append("Micro-session 30 phút: Luyện nghe chính tả các cặp số/chữ cái và bẫy -teen/-ty.")
        else:
            strengths.append("Đã ghi nhận đầy đủ danh sách câu trả lời của bạn vào hệ thống.")
            weaknesses.append("Chưa có bảng đáp án chính thức từ người học để thực hiện chấm điểm.")

        state.evaluation = EvaluationOutput(
            score_fraction=score_fraction,
            band_score=band_score,
            strengths=strengths,
            weaknesses=weaknesses,
            questions=questions,
            recommended_drills=drills
        )

        return state

    @staticmethod
    def _estimate_band_score(correct: int, total: int, skill: str) -> float:
        """Ước lượng Band score IELTS Listening / Reading theo chuẩn 40 câu"""
        if total == 0:
            return 0.0
        # Chuẩn hóa về thang 40
        scaled_40 = int(round((correct / total) * 40))
        if scaled_40 >= 39: return 9.0
        if scaled_40 >= 37: return 8.5
        if scaled_40 >= 35: return 8.0
        if scaled_40 >= 32: return 7.5
        if scaled_40 >= 30: return 7.0
        if scaled_40 >= 26: return 6.5
        if scaled_40 >= 23: return 6.0
        if scaled_40 >= 18: return 5.5
        if scaled_40 >= 16: return 5.0
        if scaled_40 >= 13: return 4.5
        if scaled_40 >= 10: return 4.0
        return 3.5

evaluator_agent = EvaluatorAgent()
