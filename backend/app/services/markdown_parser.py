import re
import yaml
from typing import List, Dict, Any, Tuple, Optional

class MarkdownParser:
    @staticmethod
    def extract_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
        """Bóc tách YAML frontmatter và phần thân Markdown"""
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return meta, body
                except Exception:
                    pass
        return {}, text

    @staticmethod
    def extract_vocab_from_markdown(content: str, source_file: str = "") -> List[Dict[str, Any]]:
        """
        Trích xuất danh sách từ vựng từ các bảng Markdown trong vocab-*.md
        Cột bảng: STT | Từ Vựng | Phiên Âm (IPA) | Loại Từ | Nghĩa Tiếng Việt | Từ Đồng Nghĩa | Collocations & Ví Dụ
        """
        meta, body = MarkdownParser.extract_frontmatter(content)
        tags = meta.get("tags", [])
        if isinstance(tags, list):
            tags_str = ", ".join(str(t) for t in tags)
        else:
            tags_str = str(tags)

        cards: List[Dict[str, Any]] = []
        lines = body.splitlines()

        table_header_found = False
        headers: List[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str.startswith("|") or not line_str.endswith("|"):
                table_header_found = False
                continue

            # Tách các cell trong hàng bảng
            cells = [c.strip() for c in line_str.strip("|").split("|")]

            # Bỏ qua hàng phân cách |--|--|
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue

            # Phát hiện hàng tiêu đề bảng
            lower_cells = [c.lower() for c in cells]
            if any("từ vựng" in c or "word" in c for c in lower_cells):
                table_header_found = True
                headers = lower_cells
                continue

            if table_header_found and len(cells) >= 4:
                # Tìm vị trí các cột
                word_idx = -1
                ipa_idx = -1
                pos_idx = -1
                meaning_idx = -1
                synonyms_idx = -1
                colloc_idx = -1

                for idx, h in enumerate(headers):
                    if "từ vựng" in h or "word" in h:
                        word_idx = idx
                    elif "phiên âm" in h or "ipa" in h:
                        ipa_idx = idx
                    elif "loại từ" in h or "pos" in h or "part" in h:
                        pos_idx = idx
                    elif "nghĩa" in h or "meaning" in h:
                        meaning_idx = idx
                    elif "đồng nghĩa" in h or "synonym" in h:
                        synonyms_idx = idx
                    elif "collocation" in h or "ví dụ" in h or "example" in h:
                        colloc_idx = idx

                # Nếu không map được theo header thì dùng vị trí mặc định 7 cột
                if word_idx == -1:
                    if len(cells) >= 7:
                        word_idx, ipa_idx, pos_idx, meaning_idx, synonyms_idx, colloc_idx = 1, 2, 3, 4, 5, 6
                    elif len(cells) >= 6:
                        word_idx, ipa_idx, pos_idx, meaning_idx, colloc_idx = 1, 2, 3, 4, 5

                def get_clean(idx: int) -> Optional[str]:
                    if 0 <= idx < len(cells):
                        val = re.sub(r"\*\*|\*", "", cells[idx]).strip()
                        return val if val else None
                    return None

                word = get_clean(word_idx)
                if not word or word.lower() in ("từ vựng", "word", "stt"):
                    continue

                ipa = get_clean(ipa_idx)
                pos = get_clean(pos_idx)
                meaning = get_clean(meaning_idx) or ""
                synonyms = get_clean(synonyms_idx)
                colloc = get_clean(colloc_idx) or ""

                # Gộp nghĩa và collocations thành mặt sau của flashcard
                back_content = meaning
                if colloc:
                    back_content += f"\n\nVí dụ & Collocations:\n{colloc.replace('<br>', '\n')}"

                cards.append({
                    "front": word,
                    "back": back_content,
                    "ipa": ipa,
                    "part_of_speech": pos,
                    "synonyms": synonyms,
                    "tags": tags_str,
                    "source_file": source_file
                })

        return cards

    @staticmethod
    def parse_test_shorthand(text: str) -> List[Dict[str, Any]]:
        """
        Bóc tách cú pháp tốc ký bài làm:
        - Đúng: '3 dentist', '12 a'
        - Sai: '1 dw137yz - dw307yz / lý do: nghe nhầm'
        - Bỏ trống: '16 - b / lý do: không kịp bắt keyword'
        """
        results: List[Dict[str, Any]] = []
        for line in text.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or line_str.startswith("|"):
                continue

            # Mẫu: 1 dw137yz - dw307yz / lý do: ...
            match_full = re.match(
                r"^(\d+)\s+([^-/]+)?\s*-\s*([^/]+?)(?:\s*/\s*(?:lý do:?\s*)?(.*))?$",
                line_str,
                re.IGNORECASE
            )
            if match_full:
                q_num = int(match_full.group(1))
                user_ans = (match_full.group(2) or "").strip()
                correct_ans = match_full.group(3).strip()
                reason = (match_full.group(4) or "").strip()
                results.append({
                    "question_number": q_num,
                    "user_answer": user_ans,
                    "correct_answer": correct_ans,
                    "is_correct": False,
                    "trap_type": reason or "Chưa phân loại",
                    "explanation": f"Lỗi sai được ghi nhận: {reason}" if reason else None
                })
                continue

            # Mẫu làm đúng hoặc chỉ nhập đáp án: '3 dentist'
            match_simple = re.match(r"^(\d+)\s+([^/]+)$", line_str)
            if match_simple:
                q_num = int(match_simple.group(1))
                user_ans = match_simple.group(2).strip()
                results.append({
                    "question_number": q_num,
                    "user_answer": user_ans,
                    "correct_answer": None,
                    "is_correct": None,
                    "trap_type": None,
                    "explanation": None
                })

        return results

markdown_parser = MarkdownParser()
