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

            # Xác định task_num: 1 hoặc 2
            task_num = 1
            if state.task_id:
                tid_lower = str(state.task_id).lower()
                if "2" in tid_lower:
                    task_num = 2
                elif "1" in tid_lower:
                    task_num = 1
            else:
                lower = raw_text.lower()
                if "task 2" in lower or "opinion" in lower or "agree or disagree" in lower:
                    task_num = 2

            # 1. Tạo nhận xét chẩn đoán bằng LLM theo 4 tiêu chí cũ
            ai_eval = self._evaluate_writing_with_llm(raw_text, task_num=task_num)

            # 2. Sinh bản sửa lỗi chi tiết từng cụm từ (Fine-grained Inline Diff) mới
            from app.services.writing_evaluator import writing_evaluator
            writing_diff = writing_evaluator.evaluate_essay(raw_text, task_num=task_num)

            # Tổng hợp nhận xét điểm mạnh / điểm yếu
            strengths = ai_eval.get("strengths") or writing_diff.strengths or [f"Đã hoàn thành bài viết Task {task_num} với độ dài {words} từ."]
            weaknesses = ai_eval.get("weaknesses") or writing_diff.weaknesses or ["Cần chú ý trau chuốt từ vựng học thuật và độ chính xác ngữ pháp."]
            drills = ai_eval.get("recommended_drills") or writing_diff.recommended_drills or [
                f"Micro-session 30p: Luyện viết lại câu theo 4 tiêu chí IELTS Writing Task {task_num}.",
                "Micro-session 35p: Mở rộng vốn từ học thuật thay cho các từ lặp lại."
            ]

            state.evaluation = EvaluationOutput(
                score_fraction=f"{words} từ (Task {task_num})",
                band_score=None,
                strengths=strengths,
                weaknesses=weaknesses,
                questions=[],
                recommended_drills=drills,
                feedback=ai_eval.get("feedback"),
                diff_html=writing_diff.diff_html,
                clean_rewritten_text=writing_diff.clean_rewritten_text,
                inline_diff_markdown=writing_diff.inline_diff_markdown,
                edits_count=writing_diff.total_edits,
                writing_correction=writing_diff.model_dump()
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
                    feedback=ai_eval.get("feedback"),
                    task_id=state.task_id or f"task-{task_num}",
                    diff_markdown=writing_diff.inline_diff_markdown,
                    clean_text=writing_diff.clean_rewritten_text
                )
                state.evaluation.updated_file = os.path.relpath(target_file, settings.CONTENT_DIR).replace("\\", "/")

            # Lưu vào PostgreSQL và tự động đồng bộ tiến độ kế hoạch tuần + flashcards
            try:
                from sqlmodel import Session, select
                from datetime import date
                from app.core.database import engine
                from app.models.test_attempt import TestAttempt
                from app.models.flashcard import Flashcard
                from app.services.plan_service import plan_service

                with Session(engine) as session:
                    attempt = TestAttempt(
                        title=f"{state.source_file or 'Bài làm Writing'} - Task {task_num}",
                        skill="writing",
                        source_file=state.source_file,
                        score=None,
                        total_questions=0,
                        band_score=None,
                        raw_attempt_text=raw_text
                    )
                    session.add(attempt)

                    # Tự động nạp các thẻ lỗi sai tiêu biểu vào Flashcards nếu có
                    if writing_diff.flashcard_candidates:
                        for fc in writing_diff.flashcard_candidates:
                            front_txt = fc.get("front", "")
                            if front_txt:
                                existing = session.exec(select(Flashcard).where(Flashcard.front == front_txt)).first()
                                if not existing:
                                    card = Flashcard(
                                        front=front_txt,
                                        back=fc.get("back", ""),
                                        tag=f"writing-task{task_num}",
                                        state=0,
                                        difficulty=5.0,
                                        stability=1.0,
                                        due_date=date.today()
                                    )
                                    session.add(card)

                    session.commit()

                plan_service.mark_task_attempt(skill="writing", source_file=state.source_file)
            except Exception as e:
                logger.error(f"Lỗi khi lưu bài làm writing hoặc đồng bộ kế hoạch: {e}", exc_info=True)

            return state

        # =====================================================================
        # 2. XỬ LÝ BÀI THI LISTENING / READING (Chấm Điểm & Đối Soát Đáp Án Cambridge 18)
        # =====================================================================
        from app.services.cambridge_key_service import cambridge_key_service

        eval_res = cambridge_key_service.evaluate_test_attempt(
            raw_text=raw_text,
            skill=state.skill,
            source_file=state.source_file
        )

        if "error" in eval_res:
            state.error = eval_res["error"]
            return state

        has_any_key = eval_res.get("has_official_key", True)
        state.has_official_key = has_any_key

        questions: List[QuestionResult] = [
            QuestionResult(
                question_number=q["question_number"],
                user_answer=q["user_answer"],
                correct_answer=q.get("correct_answer"),
                is_correct=q.get("is_correct"),
                trap_type=q.get("trap_type"),
                explanation=q.get("explanation"),
                evidence=q.get("evidence"),
                keywords=q.get("keywords")
            )
            for q in eval_res.get("questions", [])
        ]

        correct_count = sum(1 for q in questions if q.is_correct is True)
        score_fraction = eval_res.get("score_fraction")
        band_score = eval_res.get("band_score")
        feedback = eval_res.get("feedback")
        strengths = eval_res.get("strengths", [])
        weaknesses = eval_res.get("weaknesses", [])
        drills = eval_res.get("recommended_drills", [])

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

    def _evaluate_writing_with_llm(self, raw_text: str, task_num: int = 1) -> Dict[str, Any]:
        """Gọi LLM phân tích bài viết IELTS theo 4 tiêu chí chuẩn TR/TA, CC, LR, GRA (tùy biến theo Task 1 vs Task 2)"""
        from app.services.llm_service import llm_service
        words = len(raw_text.strip().split())
        try:
            if task_num == 1:
                task_label = "IELTS Writing Task 1 (Report Báo Cáo Dữ Liệu / Biểu Đồ)"
                criteria_guide = (
                    "1. Task Achievement (TA): Đánh giá Overview (tổng quan 2 xu hướng chính), lựa chọn số liệu chính xác, so sánh đối chiếu, tối thiểu 150 từ. Tuyệt đối không đưa ý kiến cá nhân vào báo cáo.\n"
                    "2. Coherence & Cohesion (CC): Nhóm số liệu logic theo đoạn (Body 1 vs Body 2), dùng liên từ nối mượt mà, tránh dùng máy móc hay lặp 'And'.\n"
                    "3. Lexical Resource (LR): Từ vựng mô tả xu hướng (surge, plummet, fluctuate, stabilize), tỷ lệ, thứ hạng, chỉ rõ lỗi chính tả và collocations Band 7.5+.\n"
                    "4. Grammatical Range & Accuracy (GRA): Bị động nội động từ (tuyệt đối không dùng 'was increased'), thì quá khứ/tương lai dự báo, mệnh đề phân từ."
                )
            else:
                task_label = "IELTS Writing Task 2 (Academic Opinion / Discussion Essay)"
                criteria_guide = (
                    "1. Task Response (TR): Trả lời đúng trọng tâm đề bài, lập trường nhất quán (clear position / thesis statement), phát triển luận điểm theo cấu trúc PEEL (Point, Explanation, Example, Link), tối thiểu 250 từ.\n"
                    "2. Coherence & Cohesion (CC): Bố cục chuẩn 4 đoạn (Introduction, 2 Thân bài, Conclusion), câu chủ đề rõ ràng, liên kết ý logic.\n"
                    "3. Lexical Resource (LR): Từ vựng học thuật theo chủ đề (Academic / Topic-specific vocabulary), collocations Band 7.5+, tránh từ ngữ thông tục.\n"
                    "4. Grammatical Range & Accuracy (GRA): Đa dạng câu phức, câu ghép, mệnh đề trạng ngữ, câu điều kiện, kiểm soát chính xác thì và dấu câu."
                )

            system_prompt = (
                f"Bạn là IELTS Senior Examiner và Writing Coach giàu kinh nghiệm chuyên chấm {task_label}. "
                "Đánh giá bài viết của người học một cách chi tiết, thẳng thắn, mang tính xây dựng cao "
                f"theo 4 tiêu chí chuẩn IELTS Writing:\n{criteria_guide}\n"
                "Định dạng phản hồi bằng Markdown rõ ràng, chuyên nghiệp."
            )
            prompt = (
                f"Dưới đây là bài viết {task_label} của người học ({words} từ):\n\n"
                f"---\n{raw_text}\n---\n\n"
                f"Hãy phân tích và đưa ra:\n"
                f"1. 📊 Đánh giá năng lực theo 4 tiêu chí IELTS cho {task_label} (Nhận xét điểm mạnh & điểm yếu cụ thể)\n"
                f"2. 🛠️ Bảng sửa lỗi ngữ pháp & câu viết chuẩn mẫu (ít nhất 2-3 câu nổi bật nhất)\n"
                f"3. 🌟 Bản viết mẫu nâng cấp (Model Rewrite) cho 1 đoạn văn tiêu biểu\n"
                f"4. 🎯 2-3 bài tập Micro-session (30-35 phút) trọng tâm tiếp theo."
            )
            feedback = llm_service.generate_text(prompt, system_message=system_prompt)
            return {
                "feedback": feedback,
                "strengths": [
                    f"Đã hoàn thành bài viết Task {task_num} thực tế với độ dài {words} từ.",
                    "Bài viết đã được lưu trữ an toàn vào hệ thống PKM."
                ],
                "weaknesses": [
                    "Cần chú ý lỗi chia thì, thể bị động và sự hòa hợp chủ vị.",
                    "Cần mở rộng vốn từ học thuật thay cho các từ lặp lại."
                ],
                "recommended_drills": [
                    f"Micro-session 30p: Luyện viết lại câu theo 4 tiêu chí IELTS Writing Task {task_num}.",
                    "Micro-session 35p: Mở rộng vốn từ học thuật và collocations nâng cao."
                ]
            }
        except Exception as e:
            logger.warning(f"Không thể gọi LLM để chấm writing (sử dụng fallback): {e}")
            return {
                "feedback": (
                    f"### 📝 Phản Hồi Bài Viết Task {task_num} ({words} từ)\n\n"
                    f"Bài viết Task {task_num} của bạn đã được lưu trữ trung thực vào hệ thống PKM. "
                    f"Bạn có thể kiểm tra cấu hình Gemini API để xem phân tích chi tiết theo 4 tiêu chí TR/TA, CC, LR, GRA."
                ),
                "strengths": [f"Đã ghi nhận bài làm Writing Task {task_num} ({words} từ) vào hệ thống PKM."],
                "weaknesses": ["Bài viết đã được lưu trữ an toàn. Hãy mở bảng chẩn đoán để xem chi tiết."],
                "recommended_drills": [f"Tập trung hoàn thiện 4 tiêu chí IELTS Writing Task {task_num}."]
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
