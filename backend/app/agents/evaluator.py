import os
import logging
from typing import List, Optional, Dict, Any
from app.agents.state import AgentState, EvaluationOutput, QuestionResult
from app.services.markdown_parser import markdown_parser
from app.services.markdown_updater import markdown_updater
from app.services.rag_engine import rag_engine
from app.core.config import settings

logger = logging.getLogger("evaluator_agent")

class EvaluatorAgent:
    """
    Evaluator Agent chuyên trách đối soát bài thi và chẩn đoán năng lực IELTS.
    Tuyệt đối tuân thủ NGUYÊN TẮC VÀNG: Không suy đoán điểm/đáp án nếu người học chưa cung cấp key.
    Lưu trữ trung thực vào PostgreSQL và cập nhật trực tiếp vào file Markdown (SSOT).
    """

    def evaluate(self, state: AgentState) -> AgentState:
        raw_text = state.input_text

        # =====================================================================
        # 1. XỬ LÝ BÀI THI WRITING (Văn bản tự do / Đoạn văn / Bài luận)
        # =====================================================================
        if state.skill.lower() == "writing":
            words = len(raw_text.strip().split())
            if words == 0:
                state.error = "Nội dung bài viết đang trống."
                return state

            state.has_official_key = False

            # Tạo nhận xét chẩn đoán bằng LLM (Gemini API qua llm_service)
            ai_eval = self._evaluate_writing_with_llm(raw_text)

            state.evaluation = EvaluationOutput(
                score_fraction=f"{words} từ",
                band_score=None,
                strengths=ai_eval.get("strengths", [f"Đã hoàn thành bài viết thực tế với độ dài {words} từ."]),
                weaknesses=ai_eval.get("weaknesses", ["Cần chú ý trau chuốt từ vựng học thuật và độ chính xác ngữ pháp."]),
                questions=[],
                recommended_drills=ai_eval.get("recommended_drills", [
                    "Micro-session 30p: Luyện viết lại câu theo 4 tiêu chí IELTS Writing.",
                    "Micro-session 35p: Mở rộng vốn từ học thuật thay cho các động từ lặp lại."
                ]),
                feedback=ai_eval.get("feedback")
            )

            # Cập nhật trực tiếp bài viết vào file Markdown (SSOT)
            target_file = markdown_updater.resolve_note_file(
                source_file=state.source_file,
                skill="writing",
                attempt_text=raw_text
            )
            if target_file:
                markdown_updater.update_writing_note(
                    file_path=target_file,
                    raw_text=raw_text,
                    feedback=ai_eval.get("feedback")
                )
                state.evaluation.updated_file = os.path.relpath(target_file, settings.CONTENT_DIR).replace("\\", "/")

            # Lưu vào PostgreSQL và tự động đồng bộ tiến độ kế hoạch tuần
            try:
                from sqlmodel import Session
                from app.core.database import engine
                from app.models.test_attempt import TestAttempt
                from app.services.plan_service import plan_service

                with Session(engine) as session:
                    attempt = TestAttempt(
                        title=state.source_file or "Bài làm Writing",
                        skill="writing",
                        source_file=state.source_file,
                        score=None,
                        total_questions=0,
                        band_score=None,
                        raw_attempt_text=raw_text
                    )
                    session.add(attempt)
                    session.commit()

                plan_service.mark_task_attempt(skill="writing", source_file=state.source_file)
            except Exception as e:
                logger.error(f"Lỗi khi lưu bài làm writing hoặc đồng bộ kế hoạch: {e}", exc_info=True)

            return state

        # =====================================================================
        # 2. XỬ LÝ BÀI THI LISTENING / READING (Cú pháp Shorthand hoặc Bảng Đáp Án)
        # =====================================================================
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
                # Đối chiếu khi người học cung cấp key
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

        # Khởi tạo nhận xét, điểm mạnh, điểm yếu & drills
        score_fraction: Optional[str] = None
        band_score: Optional[float] = None
        feedback: Optional[str] = None
        strengths: List[str] = []
        weaknesses: List[str] = []
        drills: List[str] = []

        if has_any_key and total_graded > 0:
            score_fraction = f"{correct_count}/{len(questions)}"
            band_score = self._estimate_band_score(correct_count, len(questions), state.skill)
            
            # Gọi LLM chẩn đoán chuyên sâu các câu sai
            diag = self._diagnose_mistakes_with_llm(questions, state.skill)
            feedback = diag.get("feedback")
            strengths = diag.get("strengths", [f"Hoàn thành đối soát {total_graded} câu hỏi trong bài."])
            weaknesses = diag.get("weaknesses", [])
            drills = diag.get("recommended_drills", [])
        else:
            # Tuân thủ Nguyên Tắc Vàng khi chưa có key chính thức
            strengths.append(f"Hệ thống đã lưu trữ trung thực {len(questions)} câu trả lời của bạn vào Bảng Đối Soát Bài Làm.")
            weaknesses.append("Chưa có bảng đáp án chính thức từ người học để thực hiện chấm điểm và bóc tách bẫy.")
            drills.append("Bước tiếp theo: Cung cấp bảng đáp án chính thức để kích hoạt chế độ chẩn đoán bẫy đề thi.")
            feedback = (
                f"🛡️ **Nguyên Tắc Vàng: Lưu Trữ Trung Thực Bài Làm**\n\n"
                f"Hệ thống đã ghi nhận đầy đủ **{len(questions)} câu trả lời** của bạn "
                f"vào Bảng Đối Soát Bài Làm trong ghi chú Markdown. Trợ lý AI **tuyệt đối không tự suy đoán điểm số** "
                f"hay tự phán đoán đúng/sai khi chưa có đáp án chính thức từ bạn.\n\n"
                f"👉 **Để mở khóa tính năng Chẩn Đoán Lỗi Sai & Nhận Xét Chuyên Sâu:** Hãy cung cấp đáp án chính thức "
                f"bằng cú pháp tốc ký (ví dụ: `1 sai - đúng / lý do: nghe nhầm danh từ`)."
            )

        state.evaluation = EvaluationOutput(
            score_fraction=score_fraction,
            band_score=band_score,
            strengths=strengths,
            weaknesses=weaknesses,
            questions=questions,
            recommended_drills=drills,
            feedback=feedback
        )

        # Cập nhật trực tiếp Bảng Đối Soát Bài Làm trong file Markdown (SSOT)
        target_file = markdown_updater.resolve_note_file(
            source_file=state.source_file,
            skill=state.skill,
            attempt_text=raw_text
        )
        if target_file:
            markdown_updater.update_test_table(
                file_path=target_file,
                questions=[q.model_dump() for q in questions],
                has_official_key=has_any_key
            )
            state.evaluation.updated_file = os.path.relpath(target_file, settings.CONTENT_DIR).replace("\\", "/")

        # Lưu trung thực bài làm vào PostgreSQL và tự động đồng bộ kế hoạch tuần
        try:
            from sqlmodel import Session
            from app.core.database import engine
            from app.models.test_attempt import TestAttempt, QuestionAnalysis
            from app.services.plan_service import plan_service

            with Session(engine) as session:
                attempt = TestAttempt(
                    title=state.source_file or f"Bài làm {state.skill.capitalize()}",
                    skill=state.skill,
                    source_file=state.source_file,
                    score=correct_count if has_any_key else None,
                    total_questions=len(questions),
                    band_score=band_score,
                    raw_attempt_text=raw_text
                )
                session.add(attempt)
                session.commit()
                session.refresh(attempt)

                for q in questions:
                    qa = QuestionAnalysis(
                        attempt_id=attempt.id,
                        question_number=q.question_number,
                        user_answer=q.user_answer,
                        correct_answer=q.correct_answer,
                        is_correct=q.is_correct,
                        trap_type=q.trap_type,
                        analysis=q.explanation
                    )
                    session.add(qa)
                session.commit()

            # Tự động cập nhật kế hoạch tuần theo tiến độ bài làm vừa hoàn thành
            plan_service.mark_task_attempt(skill=state.skill, source_file=state.source_file)
        except Exception as e:
            logger.error(f"Lỗi khi lưu bài làm hoặc đồng bộ kế hoạch: {e}", exc_info=True)

        return state

    def _evaluate_writing_with_llm(self, raw_text: str) -> Dict[str, Any]:
        """Gọi LLM phân tích bài viết IELTS theo 4 tiêu chí chuẩn TR/TA, CC, LR, GRA"""
        from app.services.llm_service import llm_service
        words = len(raw_text.strip().split())
        try:
            system_prompt = (
                "Bạn là IELTS Senior Examiner và Writing Coach giàu kinh nghiệm. "
                "Đánh giá bài viết của người học một cách chi tiết, thẳng thắn, mang tính xây dựng cao "
                "theo 4 tiêu chí chuẩn IELTS Writing:\n"
                "1. Task Achievement / Task Response (TR/TA)\n"
                "2. Coherence & Cohesion (CC)\n"
                "3. Lexical Resource (LR) - chỉ ra các từ sai chính tả, lỗi lặp từ và gợi ý từ vựng/collocations nâng cấp C1/Band 7.5+\n"
                "4. Grammatical Range & Accuracy (GRA) - chỉ ra lỗi ngữ pháp cụ thể và cách sửa chuẩn từng câu.\n"
                "Định dạng phản hồi bằng Markdown rõ ràng, chuyên nghiệp."
            )
            prompt = (
                f"Dưới đây là bài viết IELTS của người học ({words} từ):\n\n"
                f"---\n{raw_text}\n---\n\n"
                f"Hãy phân tích và đưa ra:\n"
                f"1. 📊 Đánh giá năng lực theo 4 tiêu chí IELTS (Nhận xét điểm mạnh & điểm yếu cụ thể)\n"
                f"2. 🛠️ Bảng sửa lỗi ngữ pháp & câu viết chuẩn mẫu (ít nhất 2-3 câu nổi bật nhất)\n"
                f"3. 🌟 Bản viết mẫu nâng cấp (Model Rewrite) cho 1 đoạn văn tiêu biểu\n"
                f"4. 🎯 2-3 bài tập Micro-session (30-35 phút) trọng tâm tiếp theo."
            )
            feedback = llm_service.generate_text(prompt, system_message=system_prompt)
            return {
                "feedback": feedback,
                "strengths": [
                    f"Đã hoàn thành bài viết thực tế với độ dài {words} từ.",
                    "Bài viết đã được lưu trữ an toàn vào hệ thống PKM."
                ],
                "weaknesses": [
                    "Cần chú ý lỗi chia thì, thể bị động và sự hòa hợp chủ vị.",
                    "Cần mở rộng vốn từ học thuật thay cho các động từ xu hướng lặp lại."
                ],
                "recommended_drills": [
                    "Micro-session 30p: Luyện viết lại các câu có cấu trúc bị động nội động từ.",
                    "Micro-session 35p: Thực hành Paraphrase các từ vựng chỉ xu hướng và số liệu."
                ]
            }
        except Exception as e:
            logger.warning(f"Không thể gọi LLM để chấm writing (sử dụng fallback): {e}")
            return {
                "feedback": (
                    f"### 📝 Phản Hồi Bài Viết ({words} từ)\n\n"
                    f"Bài viết của bạn đã được lưu trữ trung thực vào hệ thống PKM. "
                    f"Bạn có thể kết nối Gemini API để xem phân tích chi tiết theo 4 tiêu chí TR/TA, CC, LR, GRA."
                ),
                "strengths": [f"Đã ghi nhận bài làm Writing ({words} từ) vào hệ thống PKM."],
                "weaknesses": ["Bài viết đã được lưu trữ an toàn. Hãy mở bảng chẩn đoán để xem chi tiết."],
                "recommended_drills": ["Tập trung hoàn thiện 4 tiêu chí: Task Achievement, Coherence & Cohesion, Lexical Resource, GRA."]
            }

    def _diagnose_mistakes_with_llm(
        self,
        questions: List[QuestionResult],
        skill: str
    ) -> Dict[str, Any]:
        """Gọi LLM chẩn đoán bản chất bẫy đề thi và lỗi sai khi người học cung cấp đáp án chính thức"""
        from app.services.llm_service import llm_service
        wrong_questions = [q for q in questions if q.is_correct is False]
        if not wrong_questions:
            return {
                "feedback": "🎉 **Xuất sắc!** Bạn đã làm đúng toàn bộ các câu hỏi trong phần đối soát này.",
                "strengths": ["Khả năng bắt từ khóa và xử lý câu hỏi chuẩn xác."],
                "weaknesses": [],
                "recommended_drills": ["Duy trì tốc độ luyện tập 30-35 phút mỗi ngày."]
            }

        try:
            wrong_summary = "\n".join([
                f"- Câu {q.question_number}: Bạn làm '{q.user_answer}' | Đáp án đúng '{q.correct_answer}'"
                for q in wrong_questions
            ])
            system_prompt = (
                f"Bạn là IELTS Senior Examiner chuyên về kỹ năng {skill}. "
                "Nhiệm vụ của bạn là phân tích các câu làm sai của người học, chỉ ra bản chất bẫy "
                "(như bẫy âm -teen/-ty, singular/plural, paraphrase từ đồng nghĩa, distractor chuyển ý) "
                "và đưa ra lời khuyên khắc phục súc tích, thực chiến."
            )
            prompt = (
                f"Dưới đây là danh sách các câu làm sai trong bài thi IELTS {skill}:\n"
                f"{wrong_summary}\n\n"
                "Hãy đưa ra:\n"
                "1. Điểm mạnh và điểm yếu tổng quan của người học\n"
                "2. Phân tích nguyên nhân mắc bẫy của từng câu sai trên\n"
                "3. 2 bài tập micro-session (30-35 phút) để khắc phục triệt để các bẫy này."
            )
            feedback = llm_service.generate_text(prompt, system_message=system_prompt)
            return {
                "feedback": feedback,
                "strengths": [f"Hoàn thành đối soát {len(questions)} câu trong bài thi."],
                "weaknesses": [f"Mắc bẫy ở {len(wrong_questions)} câu: chủ yếu về ngữ âm/paraphrase/bẫy chuyển ý."],
                "recommended_drills": [
                    f"Micro-session 30p: Nghe lại/Đọc lại đoạn văn chứa các câu sai ({', '.join([str(q.question_number) for q in wrong_questions[:5]])}).",
                    "Micro-session 35p: Ghi chú các cặp từ paraphrase vào sổ từ vựng."
                ]
            }
        except Exception as e:
            logger.warning(f"Lỗi khi gọi LLM chẩn đoán lỗi sai {skill}: {e}")
            return {
                "feedback": None,
                "strengths": [f"Hoàn thành đối soát {len(questions)} câu hỏi trong bài."],
                "weaknesses": [f"Có {len(wrong_questions)} câu cần xem lại bẫy đề thi."],
                "recommended_drills": ["Micro-session 30 phút: Luyện nghe chính tả / bóc tách keyword mapping."]
            }

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
