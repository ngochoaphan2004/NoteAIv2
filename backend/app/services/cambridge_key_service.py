import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("cambridge_key_service")

class CambridgeKeyService:
    """
    Dịch vụ quản lý và đối soát đáp án chính thức Cambridge IELTS 18
    từ cơ sở dữ liệu JSON (content/data/cambridge_18_answers_and_explanations.json).
    """

    def __init__(self):
        self._keys_db: Dict[Tuple[int, str, int], Dict[str, Any]] = {}
        self._loaded = False
        self._load_keys()

    def _find_json_path(self) -> Optional[str]:
        # Ưu tiên content/data (SSOT trong dự án)
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "content", "data", "cambridge_18_answers_and_explanations.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "cambridge_18_answers_and_explanations.json"),
            os.path.join(os.getcwd(), "content", "data", "cambridge_18_answers_and_explanations.json"),
            os.path.join(os.getcwd(), "data", "cambridge_18_answers_and_explanations.json"),
        ]
        for c in candidates:
            abs_p = os.path.abspath(c)
            if os.path.isfile(abs_p):
                return abs_p
        return None

    def _load_keys(self):
        json_path = self._find_json_path()
        if not json_path:
            logger.warning("Không tìm thấy tệp cambridge_18_answers_and_explanations.json!")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            tests = data.get("tests", {})
            for test_key, test_data in tests.items():
                test_num = test_data.get("test", 1)

                # Nạp Listening
                for q in test_data.get("listening", []):
                    q_num = q.get("question_number")
                    if q_num is not None:
                        self._keys_db[(test_num, "listening", int(q_num))] = q
                        count += 1

                # Nạp Reading
                for q in test_data.get("reading", []):
                    q_num = q.get("question_number")
                    if q_num is not None:
                        self._keys_db[(test_num, "reading", int(q_num))] = q
                        count += 1

            self._loaded = True
            logger.info(f"Đã nạp thành công {count} câu hỏi đáp án chính thức Cambridge 18 từ: {json_path}")
        except Exception as e:
            logger.error(f"Lỗi khi nạp dữ liệu đáp án Cambridge 18: {e}", exc_info=True)

    def get_question_info(self, test_num: int, skill: str, question_number: int) -> Optional[Dict[str, Any]]:
        """Lấy thông tin đáp án và giải thích cho một câu hỏi cụ thể"""
        skill_norm = skill.lower().strip()
        return self._keys_db.get((test_num, skill_norm, question_number))

    def detect_test_number(self, source_file: Optional[str] = None, attempt_text: Optional[str] = None) -> int:
        """Tự động phát hiện số thứ tự Test (1, 2, 3, 4) từ tên file hoặc nội dung bài làm"""
        combined = f"{source_file or ''} {attempt_text or ''}".lower()
        m = re.search(r"test[-_\s]*([1-4])\b", combined)
        if m:
            return int(m.group(1))
        return 1  # Mặc định là Test 1 (theo kế hoạch tuần hiện tại)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Chuẩn hóa chuỗi văn bản: chữ thường, xóa khoảng trắng thừa, xóa dấu câu thừa"""
        if not text:
            return ""
        t = text.lower().strip()
        t = re.sub(r"[`'\"“”‘’.,;:]", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    @classmethod
    def get_acceptable_variants(cls, official_answer: str) -> List[str]:
        """
        Sinh danh sách các biến thể đáp án hợp lệ được Cambridge chấp nhận:
        - Xử lý ngoặc đơn tùy chọn: '24(th) April' -> ['24th april', '24 april']
        - Xử lý '(food) consumption' -> ['food consumption', 'consumption']
        - Xử lý gạch chéo: 'A / B' hoặc 'A or B' -> ['a', 'b']
        - Xử lý mã bưu điện: 'DW307YZ' -> ['dw307yz', 'dw 307 yz']
        """
        if not official_answer:
            return []

        raw = official_answer.strip()
        variants = set()

        # Biến thể gốc chuẩn hóa
        norm_raw = cls.normalize_text(raw)
        variants.add(norm_raw)

        # Xử lý dấu gạch chéo hoặc 'or': 'supermarket / market' hoặc 'A or B'
        split_parts = re.split(r"\s*/\s*|\s+or\s+", raw, flags=re.IGNORECASE)
        if len(split_parts) > 1:
            for p in split_parts:
                variants.add(cls.normalize_text(p))

        # Xử lý các từ trong ngoặc đơn (optional words): '24(th) April' hoặc '(food) consumption'
        # Dạng 1: bỏ toàn bộ phần trong ngoặc: '24 April' hoặc 'consumption'
        without_parens = re.sub(r"\([^)]*\)", "", raw)
        variants.add(cls.normalize_text(without_parens))

        # Dạng 2: giữ lại nội dung trong ngoặc: '24th April' hoặc 'food consumption'
        with_parens_content = re.sub(r"[()]", "", raw)
        variants.add(cls.normalize_text(with_parens_content))

        # Xử lý True/False/Not Given & Yes/No
        if norm_raw in ["true", "t"]:
            variants.update(["true", "t"])
        elif norm_raw in ["false", "f"]:
            variants.update(["false", "f"])
        elif norm_raw in ["not given", "ng"]:
            variants.update(["not given", "ng"])
        elif norm_raw in ["yes", "y"]:
            variants.update(["yes", "y"])
        elif norm_raw in ["no", "n"]:
            variants.update(["no", "n"])

        # Xử lý mã bưu chính / mã số không khoảng trắng: 'dw307yz' <=> 'dw 307 yz'
        no_spaces = re.sub(r"\s+", "", norm_raw)
        variants.add(no_spaces)

        return [v for v in variants if v]

    @classmethod
    def match_answer(cls, user_answer: str, official_answer: str) -> bool:
        """Đối chiếu câu trả lời của người học với đáp án chính thức Cambridge"""
        if not user_answer or not official_answer:
            return False

        u_norm = cls.normalize_text(user_answer)
        u_no_space = re.sub(r"\s+", "", u_norm)

        acceptable = cls.get_acceptable_variants(official_answer)

        # Kiểm tra khớp chính xác với bất kỳ biến thể nào
        for variant in acceptable:
            if u_norm == variant:
                return True
            if u_no_space == re.sub(r"\s+", "", variant):
                return True

        # Đối với các câu trắc nghiệm A, B, C, D: cho phép 'A.', '(A)', 'A'
        m_user = re.match(r"^\(?([a-h])[\)\.]?$", u_norm)
        m_off = re.match(r"^\(?([a-h])[\)\.]?$", cls.normalize_text(official_answer))
        if m_user and m_off:
            return m_user.group(1) == m_off.group(1)

        return False

    @staticmethod
    def estimate_band_score(correct_count: int, total_questions: int, skill: str) -> float:
        """
        Ước lượng Band Score IELTS chuẩn xác dựa trên thang điểm 40 câu của Cambridge.
        Tự động quy đổi tỷ lệ nếu bài làm là micro-session (10 câu, 13 câu, 20 câu, v.v.).
        """
        if total_questions <= 0 or correct_count <= 0:
            return 0.0

        # Chuẩn hóa về thang 40 câu
        scaled_correct = round((correct_count / total_questions) * 40)

        # Thang điểm chuẩn Cambridge IELTS Listening / Academic Reading
        if scaled_correct >= 39:
            return 9.0
        elif scaled_correct >= 37:
            return 8.5
        elif scaled_correct >= 35:
            return 8.0
        elif scaled_correct >= 32:
            return 7.5
        elif scaled_correct >= 30:
            return 7.0
        elif scaled_correct >= 26:
            return 6.5
        elif scaled_correct >= 23:
            return 6.0
        elif scaled_correct >= 18:
            return 5.5
        elif scaled_correct >= 16:
            return 5.0
        elif scaled_correct >= 13:
            return 4.5
        elif scaled_correct >= 10:
            return 4.0
        elif scaled_correct >= 7:
            return 3.5
        else:
            return 3.0

    def evaluate_test_attempt(
        self,
        raw_text: str,
        skill: str,
        source_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chấm điểm và đối soát bài thi dựa trên đáp án chính thức Cambridge 18.
        Trả về kết quả chi tiết từng câu hỏi, giải thích, dẫn chứng và Band Score.
        """
        from app.services.markdown_parser import markdown_parser

        skill_norm = skill.lower().strip()
        test_num = self.detect_test_number(source_file, raw_text)

        # Phân tích cú pháp bài làm của người học
        parsed_items = markdown_parser.parse_test_shorthand(raw_text)
        if not parsed_items:
            # Fallback nếu parse_test_shorthand không bắt được
            parsed_items = []
            for line in raw_text.splitlines():
                m = re.match(r"^\s*(\d+)[\.\:\-\s]+(.+)$", line.strip())
                if m:
                    parsed_items.append({
                        "question_number": int(m.group(1)),
                        "user_answer": m.group(2).strip(),
                        "correct_answer": None
                    })

        if not parsed_items:
            return {
                "error": "Không tìm thấy câu trả lời nào hợp lệ trong bài làm."
            }

        questions_result = []
        correct_count = 0
        total_questions = len(parsed_items)

        for item in parsed_items:
            q_num = item["question_number"]
            user_ans = item["user_answer"]

            # Tra cứu trong cơ sở dữ liệu đáp án Cambridge 18
            q_info = self.get_question_info(test_num, skill_norm, q_num)

            if q_info:
                official_ans = q_info.get("answer", "")
                explanation = q_info.get("explanation", "")
                evidence = q_info.get("evidence", "")
                trap_type = q_info.get("question_type", "")
                keywords = q_info.get("keywords", [])

                # Đối chiếu câu trả lời
                is_correct = self.match_answer(user_ans, official_ans)
                if is_correct:
                    correct_count += 1

                questions_result.append({
                    "question_number": q_num,
                    "user_answer": user_ans,
                    "correct_answer": official_ans,
                    "is_correct": is_correct,
                    "trap_type": trap_type,
                    "explanation": explanation,
                    "evidence": evidence,
                    "keywords": keywords,
                    "part": q_info.get("part")
                })
            else:
                # Không tìm thấy trong key Cambridge (custom / ngoài đề)
                is_correct = None
                corr_from_item = item.get("correct_answer")
                if corr_from_item:
                    is_correct = self.match_answer(user_ans, corr_from_item)
                    if is_correct:
                        correct_count += 1

                questions_result.append({
                    "question_number": q_num,
                    "user_answer": user_ans,
                    "correct_answer": corr_from_item,
                    "is_correct": is_correct,
                    "trap_type": item.get("trap_type", "Tự luận / Tự check"),
                    "explanation": item.get("explanation", ""),
                    "evidence": "",
                    "keywords": [],
                    "part": None
                })

        score_fraction = f"{correct_count}/{total_questions}"
        band_score = self.estimate_band_score(correct_count, total_questions, skill_norm)

        # Xây dựng báo cáo chẩn đoán lỗi sai từ đáp án Cambridge
        incorrect_questions = [q for q in questions_result if q.get("is_correct") is False]
        correct_questions = [q for q in questions_result if q.get("is_correct") is True]

        strengths = []
        if correct_questions:
            strengths.append(
                f"Làm đúng xuất sắc {len(correct_questions)}/{total_questions} câu: "
                f"{', '.join(['Câu ' + str(q['question_number']) for q in correct_questions[:8]])}"
                + (f" và {len(correct_questions) - 8} câu khác." if len(correct_questions) > 8 else ".")
            )
        else:
            strengths.append("Đã hoàn thành và nộp đầy đủ bài làm đối soát.")

        weaknesses = []
        recommended_drills = []

        if incorrect_questions:
            weak_summary = []
            for q in incorrect_questions[:5]:
                q_num = q["question_number"]
                q_off = q["correct_answer"]
                q_user = q["user_answer"]
                q_exp = q.get("explanation", "")
                weak_summary.append(f"• **Câu {q_num}:** Bạn điền `{q_user}` ➜ Đáp án đúng: **`{q_off}`**.\n  _Phân tích:_ {q_exp}")

            weaknesses.extend(weak_summary)

            # Đề xuất Micro-drills tương ứng với các dạng bài bị sai
            missed_types = set(q.get("trap_type") for q in incorrect_questions if q.get("trap_type"))
            for m_type in missed_types:
                recommended_drills.append(
                    f"Micro-session 30p: Ôn luyện chuyên sâu dạng bài '{m_type}' ({skill_norm.capitalize()}) và rèn kỹ năng bắt từ khóa đồng nghĩa (Paraphrasing)."
                )
            recommended_drills.append(
                "Micro-session 35p: Xem lại Audio Script / Đoạn trích dẫn bài đọc của các câu làm sai để ghi chú các bẫy âm và cấu trúc ngữ pháp mới."
            )
        else:
            weaknesses.append("Không có lỗi sai nào! Toàn bộ các câu trả lời đều khớp hoàn toàn với đáp án Cambridge.")
            recommended_drills.append("Duy trì tốc độ làm bài và chuyển sang luyện tập các phần tiếp theo trong kế hoạch tuần.")

        feedback_parts = [
            f"🎯 **KẾT QUẢ CHẤM ĐIỂM CHÍNH THỨC (CAMBRIDGE 18 - TEST {test_num} {skill_norm.upper()})**",
            f"• Số câu đúng: **{score_fraction}** (Tỷ lệ chính xác: {round(correct_count / total_questions * 100)}%)",
            f"• Ước lượng Band Score: **{band_score}**",
            ""
        ]

        if incorrect_questions:
            feedback_parts.append(f"🔍 **CHI TIẾT {len(incorrect_questions)} CÂU CẦN RÚT KINH NGHIỆM:**")
            for q in incorrect_questions:
                q_num = q["question_number"]
                q_off = q["correct_answer"]
                q_user = q["user_answer"]
                q_exp = q.get("explanation", "")
                q_evi = q.get("evidence", "")

                evi_text = f"\n  _Dẫn chứng:_ \"{q_evi}\"" if q_evi else ""
                feedback_parts.append(
                    f"- **Câu {q_num}:** Bài làm: `{q_user}` | Đáp án chuẩn: **`{q_off}`**\n"
                    f"  _Giải thích:_ {q_exp}{evi_text}"
                )
        else:
            feedback_parts.append("🎉 **Chúc mừng! Bạn đã làm đúng tuyệt đối toàn bộ các câu trong phần thi này!**")

        feedback = "\n".join(feedback_parts)

        return {
            "test_number": test_num,
            "skill": skill_norm,
            "score_fraction": score_fraction,
            "band_score": band_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "questions": questions_result,
            "recommended_drills": recommended_drills,
            "feedback": feedback,
            "has_official_key": True
        }

cambridge_key_service = CambridgeKeyService()
