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

    def _find_data_dirs(self) -> List[str]:
        # Ưu tiên thư mục data gốc của dự án (D:\Ielts\code\NoteAI.v2\data)
        candidates = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")),
            os.path.abspath(os.path.join(os.getcwd(), "data")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "content", "data")),
            os.path.abspath(os.path.join(os.getcwd(), "content", "data")),
        ]
        valid_dirs = []
        seen = set()
        for c in candidates:
            if c not in seen and os.path.isdir(c):
                seen.add(c)
                valid_dirs.append(c)
        return valid_dirs

    def _load_keys(self):
        data_dirs = self._find_data_dirs()
        if not data_dirs:
            logger.warning("Không tìm thấy thư mục data chứa đáp án Cambridge 18!")
            return

        total_loaded = 0

        # 1. Nạp từ file tổng hợp cambridge_18_answers_and_explanations.json
        for d in data_dirs:
            full_json = os.path.join(d, "cambridge_18_answers_and_explanations.json")
            if os.path.isfile(full_json):
                try:
                    with open(full_json, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    tests = data.get("tests", {})
                    for test_key, test_data in tests.items():
                        test_num = test_data.get("test", 1)

                        for q in test_data.get("listening", []):
                            q_num = q.get("question_number")
                            if q_num is not None:
                                key = (test_num, "listening", int(q_num))
                                if key not in self._keys_db:
                                    self._keys_db[key] = q
                                    total_loaded += 1

                        for q in test_data.get("reading", []):
                            q_num = q.get("question_number")
                            if q_num is not None:
                                key = (test_num, "reading", int(q_num))
                                if key not in self._keys_db:
                                    self._keys_db[key] = q
                                    total_loaded += 1

                    logger.info(f"Đã nạp {total_loaded} câu hỏi từ: {full_json}")
                    break
                except Exception as e:
                    logger.error(f"Lỗi khi đọc file {full_json}: {e}", exc_info=True)

        # 2. Bổ sung từ các file riêng lẻ cambridge18_test_*.json trong data/ nếu có
        for d in data_dirs:
            for i in range(1, 5):
                indiv_file = os.path.join(d, f"cambridge18_test_{i}.json")
                if os.path.isfile(indiv_file):
                    try:
                        with open(indiv_file, "r", encoding="utf-8") as f:
                            t_data = json.load(f)
                        test_num = t_data.get("test", i)

                        for q in t_data.get("listening", []):
                            q_num = q.get("question_number")
                            if q_num is not None:
                                key = (test_num, "listening", int(q_num))
                                if key not in self._keys_db:
                                    self._keys_db[key] = q
                                    total_loaded += 1

                        for q in t_data.get("reading", []):
                            q_num = q.get("question_number")
                            if q_num is not None:
                                key = (test_num, "reading", int(q_num))
                                if key not in self._keys_db:
                                    self._keys_db[key] = q
                                    total_loaded += 1
                    except Exception as e:
                        logger.warning(f"Lỗi khi nạp file riêng lẻ {indiv_file}: {e}")

        if total_loaded > 0:
            self._loaded = True
            logger.info(f"Tổng cộng đã nạp thành công {len(self._keys_db)} câu hỏi đáp án Cambridge 18 từ data/")
        else:
            logger.warning("Không có câu hỏi nào được nạp từ các thư mục data!")

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

    @staticmethod
    def _clean_stem(txt: str) -> str:
        """Loại bỏ các hậu tố '(Option 1)', '(Select 1 of 2)' để so khớp gốc câu hỏi"""
        t = re.sub(r"\s*\((?:option|select|first|second|\d+ of \d+)[^)]*\)", "", txt, flags=re.IGNORECASE)
        t = re.sub(r"\s+", " ", t).strip().lower()
        return t

    def get_question_group(self, test_num: int, skill: str, q_num: int) -> List[int]:
        """
        Phát hiện nếu câu hỏi nằm trong nhóm multi-select (ví dụ cặp câu 'Choose TWO letters' như Q14 & Q15).
        Trả về danh sách số thứ tự câu hỏi trong cùng nhóm (ví dụ [14, 15]).
        """
        curr = self.get_question_info(test_num, skill, q_num)
        if not curr:
            return [q_num]
        stem = self._clean_stem(curr.get("question_text", ""))
        is_multi = "two" in stem or "three" in stem or "choose" in stem
        if not is_multi:
            return [q_num]

        group = [q_num]
        prev_info = self.get_question_info(test_num, skill, q_num - 1)
        if prev_info:
            prev_stem = self._clean_stem(prev_info.get("question_text", ""))
            if (prev_stem == stem) or (("two" in prev_stem or "three" in prev_stem) and is_multi):
                group.insert(0, q_num - 1)

        next_info = self.get_question_info(test_num, skill, q_num + 1)
        if next_info:
            next_stem = self._clean_stem(next_info.get("question_text", ""))
            if (next_stem == stem) or (("two" in next_stem or "three" in next_stem) and is_multi):
                group.append(q_num + 1)

        return sorted(list(set(group)))

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

        # Xử lý theo từng nhóm câu hỏi (hỗ trợ các câu 'Choose TWO letters' đảo thứ tự tự do)
        processed_q_nums = set()
        items_by_q = {it["question_number"]: it for it in parsed_items}

        for item in parsed_items:
            q_num = item["question_number"]
            if q_num in processed_q_nums:
                continue

            group_nums = self.get_question_group(test_num, skill_norm, q_num)
            group_items = [items_by_q[qn] for qn in group_nums if qn in items_by_q]

            if len(group_items) > 1 and len(group_nums) > 1:
                # Nhóm câu hỏi chọn nhiều đáp án: thu thập tập hợp đáp án chính thức khả dụng
                avail_answers = []
                group_infos = {}
                for gn in group_nums:
                    info = self.get_question_info(test_num, skill_norm, gn)
                    if info:
                        group_infos[gn] = info
                        ans_raw = info.get("answer", "")
                        for part in re.split(r"[,/]", ans_raw):
                            clean_part = part.strip()
                            if clean_part and clean_part not in avail_answers:
                                avail_answers.append(clean_part)

                used_answers = set()
                for g_item in group_items:
                    gn = g_item["question_number"]
                    u_ans = g_item["user_answer"]
                    q_info = group_infos.get(gn) or self.get_question_info(test_num, skill_norm, gn)

                    matched_ans = None
                    for a in avail_answers:
                        if a not in used_answers and self.match_answer(u_ans, a):
                            matched_ans = a
                            break

                    is_correct = False
                    if matched_ans:
                        is_correct = True
                        used_answers.add(matched_ans)
                        correct_count += 1

                    official_display = ", ".join(avail_answers) if avail_answers else (q_info.get("answer", "") if q_info else "")
                    explanation = q_info.get("explanation", "") if q_info else ""
                    evidence = q_info.get("evidence", "") if q_info else ""
                    trap_type = q_info.get("question_type", "Multiple choice") if q_info else "Multiple choice"

                    questions_result.append({
                        "question_number": gn,
                        "user_answer": u_ans,
                        "correct_answer": official_display,
                        "is_correct": is_correct,
                        "trap_type": trap_type,
                        "explanation": explanation,
                        "evidence": evidence,
                        "keywords": q_info.get("keywords", []) if q_info else [],
                        "part": q_info.get("part") if q_info else None
                    })
                    processed_q_nums.add(gn)
            else:
                # Câu hỏi đơn lẻ bình thường
                processed_q_nums.add(q_num)
                user_ans = item["user_answer"]
                q_info = self.get_question_info(test_num, skill_norm, q_num)

                if q_info:
                    official_ans = q_info.get("answer", "")
                    explanation = q_info.get("explanation", "")
                    evidence = q_info.get("evidence", "")
                    trap_type = q_info.get("question_type", "")
                    keywords = q_info.get("keywords", [])

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
