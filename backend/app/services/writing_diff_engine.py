import re
import html
from typing import List, Tuple, Dict, Any
from app.schemas.writing_correction import InlineEdit, SentenceCorrection, ErrorCategory

class WritingDiffEngine:
    """
    Deterministic Diff & Alignment Engine for IELTS Writing.
    Chịu trách nhiệm:
    1. Chèn chính xác các huy hiệu 🔴 [Gạch ngang text cũ] ➜ 🟢 [In đậm text mới] vào văn bản gốc.
    2. Sinh định dạng HTML tương tác (kèm tooltip giải thích) và định dạng Markdown (lưu trữ SSOT).
    3. Tạo bản bài viết hoàn chỉnh sạch sẽ (Clean Rewritten Text).
    """

    @staticmethod
    def _escape(text: str) -> str:
        return html.escape(text, quote=True)

    @classmethod
    def apply_edits_to_sentence(
        cls,
        sentence: str,
        edits: List[InlineEdit]
    ) -> Tuple[str, str, str]:
        """
        Áp dụng danh sách edits vào một câu đơn lẻ.
        Trả về: (diff_html, diff_markdown, clean_sentence)
        """
        if not edits:
            escaped = cls._escape(sentence)
            return escaped, sentence, sentence

        # Sắp xếp các edit theo thứ tự xuất hiện trong câu để tránh chồng chéo
        # Tìm vị trí xuất hiện của từng original trong sentence
        indexed_edits: List[Tuple[int, int, InlineEdit]] = []
        lowered_sentence = sentence.lower()
        search_cursor = 0

        for edit in edits:
            orig = edit.original.strip()
            if not orig:
                continue

            # Ưu tiên tìm với word boundary (?<!\w) ... (?!\w) để tránh match subword (ví dụ 'come' trong 'become')
            pat = r"(?<!\w)" + re.escape(orig) + r"(?!\w)"
            matches = list(re.finditer(pat, sentence, re.IGNORECASE))
            if matches:
                chosen = next((m for m in matches if m.start() >= search_cursor), matches[0])
                indexed_edits.append((chosen.start(), chosen.end(), edit))
                search_cursor = max(search_cursor, chosen.end())
            else:
                # Fallback: substring search nếu có ký tự đặc biệt không khớp boundary
                pos = lowered_sentence.find(orig.lower(), search_cursor)
                if pos != -1:
                    end_pos = pos + len(orig)
                    indexed_edits.append((pos, end_pos, edit))
                    search_cursor = end_pos
                else:
                    pos_anywhere = lowered_sentence.find(orig.lower())
                    if pos_anywhere != -1:
                        indexed_edits.append((pos_anywhere, pos_anywhere + len(orig), edit))

        # Sắp xếp theo vị trí bắt đầu
        indexed_edits.sort(key=lambda x: x[0])

        # Loại bỏ các khoảng bị chồng lấn (overlapping intervals)
        non_overlapping: List[Tuple[int, int, InlineEdit]] = []
        last_end = -1
        for start, end, edit in indexed_edits:
            if start >= last_end:
                non_overlapping.append((start, end, edit))
                last_end = end

        # Xây dựng 3 chuỗi kết quả
        html_parts: List[str] = []
        md_parts: List[str] = []
        clean_parts: List[str] = []

        cur_idx = 0
        for start, end, edit in non_overlapping:
            # Đoạn văn bản bình thường trước lỗi
            if start > cur_idx:
                segment = sentence[cur_idx:start]
                html_parts.append(cls._escape(segment))
                md_parts.append(segment)
                clean_parts.append(segment)

            actual_orig = sentence[start:end]
            repl = edit.replacement.strip()
            cat_val = edit.category.value if hasattr(edit.category, "value") else str(edit.category)
            crit_val = edit.criteria.value if hasattr(edit.criteria, "value") else str(edit.criteria)
            exp_text = cls._escape(edit.explanation_vi or f"Nâng cấp chuẩn {crit_val}")

            # 1. HTML Diff Pill
            pill_html = (
                f'<span class="ielts-diff-pill" data-category="{cat_val}" data-criteria="{crit_val}" title="{exp_text}">'
                f'<span class="ielts-diff-del">🔴 <del>{cls._escape(actual_orig)}</del></span>'
                f'<span class="ielts-diff-arrow"> ➜ </span>'
                f'<span class="ielts-diff-ins">🟢 <ins>{cls._escape(repl)}</ins></span>'
                f'</span>'
            )
            html_parts.append(pill_html)

            # 2. Markdown Diff
            pill_md = f"🔴 ~~{actual_orig}~~ ➜ 🟢 **{repl}**"
            md_parts.append(pill_md)

            # 3. Clean Text
            clean_parts.append(repl)

            cur_idx = end

        # Đoạn văn bản còn lại sau edit cuối cùng
        if cur_idx < len(sentence):
            tail = sentence[cur_idx:]
            html_parts.append(cls._escape(tail))
            md_parts.append(tail)
            clean_parts.append(tail)

        return "".join(html_parts), "".join(md_parts), "".join(clean_parts)

    @classmethod
    def render_full_essay(
        cls,
        sentences: List[SentenceCorrection]
    ) -> Tuple[str, str, str]:
        """
        Render toàn bộ bài viết từ danh sách các câu đã phân tích.
        Trả về: (diff_html, inline_diff_markdown, clean_rewritten_text)
        """
        html_sentences: List[str] = []
        md_sentences: List[str] = []
        clean_sentences: List[str] = []

        for s in sentences:
            s_html, s_md, s_clean = cls.apply_edits_to_sentence(s.original_sentence, s.edits)
            html_sentences.append(s_html)
            md_sentences.append(s_md)
            clean_sentences.append(s_clean)

        full_html = " ".join(html_sentences)
        full_md = " ".join(md_sentences)
        full_clean = " ".join(clean_sentences)

        return full_html, full_md, full_clean

    @classmethod
    def extract_flashcard_candidates(
        cls,
        sentences: List[SentenceCorrection]
    ) -> List[Dict[str, str]]:
        """
        Trích xuất các lỗi sai có giá trị học thuật cao (collocation, grammar, preposition)
        để tự động đồng bộ vào CSDL Flashcards phục vụ thuật toán Spaced Repetition FSRS.
        """
        cards = []
        seen = set()

        for s in sentences:
            for e in s.edits:
                orig = e.original.strip()
                repl = e.replacement.strip()
                if not orig or not repl or orig.lower() == repl.lower():
                    continue

                key = (orig.lower(), repl.lower())
                if key in seen:
                    continue
                seen.add(key)

                # Chỉ trích xuất các lỗi mang tính cấu trúc và cụm từ
                cat_val = e.category.value if hasattr(e.category, "value") else str(e.category)
                crit_val = e.criteria.value if hasattr(e.criteria, "value") else str(e.criteria)
                
                # Tạo ngữ cảnh câu với chỗ trống
                context_sentence = s.original_sentence.replace(orig, f"[... {orig} ❌ ...]")

                cards.append({
                    "front": f"[{cat_val.upper()}] Trong IELTS Writing, cụm từ đúng thay cho '{orig}' là gì?\n\nNgữ cảnh: \"{context_sentence}\"",
                    "back": f"✅ **{repl}**\n\n📌 **Tiêu chí:** {crit_val}\n💡 **Giải thích:** {e.explanation_vi}",
                    "word": repl,
                    "category": cat_val,
                    "criteria": crit_val
                })

        return cards

writing_diff_engine = WritingDiffEngine()
