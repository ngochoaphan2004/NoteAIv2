import os
import re
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("markdown_updater")

class MarkdownNoteUpdater:
    """
    Dịch vụ cập nhật trung thực bài làm của người học vào Bảng Đối Soát Bài Làm 
    trong các file ghi chú Markdown (.md) theo đúng tôn chỉ Single Source of Truth (SSOT).
    """

    @staticmethod
    def resolve_note_file(
        source_file: Optional[str] = None,
        skill: str = "listening",
        attempt_text: str = ""
    ) -> Optional[str]:
        """
        Xác định đường dẫn tuyệt đối của file Markdown cần cập nhật trong CONTENT_DIR.
        """
        content_dir = settings.CONTENT_DIR

        # 1. Thử phân giải trực tiếp từ source_file
        if source_file:
            cleaned = source_file.strip().replace("\\", "/").lstrip("/")
            # Bỏ prefix content/ nếu có
            if cleaned.startswith("content/"):
                cleaned = cleaned[len("content/"):]

            candidates = [
                os.path.join(content_dir, cleaned),
                os.path.join(content_dir, f"{cleaned}.md"),
                os.path.join(content_dir, f"{cleaned}/index.md")
            ]
            for cand in candidates:
                if os.path.isfile(cand):
                    return cand

            # Tìm kiếm theo tên file trong toàn bộ content_dir
            target_name = os.path.basename(cleaned)
            if not target_name.endswith(".md"):
                target_name += ".md"

            for root, _, files in os.walk(content_dir):
                if target_name in files:
                    return os.path.join(root, target_name)

        # 2. Thử nhận diện theo nội dung văn bản (attempt_text)
        lower_text = attempt_text.lower()
        if "listening" in lower_text:
            cand = os.path.join(content_dir, "plans", "week-01", "test-1-listening.md")
            if os.path.isfile(cand):
                return cand
        elif "reading" in lower_text or "passage 3" in lower_text or "space junk" in lower_text:
            cand = os.path.join(content_dir, "plans", "week-01", "test-1-reading-p3.md")
            if os.path.isfile(cand):
                return cand
        elif "writing" in lower_text or "task 1" in lower_text or "urban" in lower_text:
            cand = os.path.join(content_dir, "plans", "week-01", "test-1-writing.md")
            if os.path.isfile(cand):
                return cand

        # 3. Fallback theo kỹ năng (skill)
        skill_lower = (skill or "listening").lower()
        if skill_lower == "listening":
            default_path = os.path.join(content_dir, "plans", "week-01", "test-1-listening.md")
        elif skill_lower == "reading":
            default_path = os.path.join(content_dir, "plans", "week-01", "test-1-reading-p3.md")
        elif skill_lower == "writing":
            default_path = os.path.join(content_dir, "plans", "week-01", "test-1-writing.md")
        else:
            default_path = os.path.join(content_dir, "template-test-attempt.md")

        if os.path.isfile(default_path):
            return default_path

        return None

    @classmethod
    def update_test_table(
        cls,
        file_path: str,
        questions: List[Dict[str, Any]],
        has_official_key: bool = False
    ) -> bool:
        """
        Cập nhật câu trả lời của người học vào Bảng Đối Soát Bài Làm trong file Markdown.
        """
        if not os.path.isfile(file_path):
            logger.warning(f"[MARKDOWN UPDATER] Không tìm thấy file: {file_path}")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()
            questions_map = {q["question_number"]: q for q in questions}
            updated_count = 0
            new_lines = []

            for line in lines:
                m = re.match(r"^\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|(.*)\|\s*$", line)
                if not m:
                    new_lines.append(line)
                    continue

                q_num = int(m.group(1))
                if q_num not in questions_map:
                    new_lines.append(line)
                    continue

                q_data = questions_map[q_num]
                cells = [c.strip() for c in line.split("|")[1:-1]]

                user_ans = q_data.get("user_answer", "").strip()
                corr_ans = (q_data.get("correct_answer") or "").strip()
                is_corr = q_data.get("is_correct")
                trap = (q_data.get("trap_type") or "").strip()
                exp = (q_data.get("explanation") or "").strip()

                note = f"{trap}: {exp}".strip(": ") if (trap or exp) else ""

                # Định dạng bảng 5 cột: | STT | Bài Làm Lúc Thi | Đáp Án Chính Thức | Kết Quả | Ghi Chú |
                if len(cells) >= 5:
                    cells[0] = f"**{q_num}**"
                    if user_ans:
                        cells[1] = f"`{user_ans}`"
                    if corr_ans:
                        cells[2] = corr_ans
                    
                    if is_corr is True:
                        cells[3] = "✅"
                    elif is_corr is False:
                        cells[3] = "❌"
                    else:
                        cells[3] = "⚪"

                    if note:
                        cells[4] = note
                    elif not cells[4]:
                        cells[4] = ""

                    parts = [f" {c.strip()} " if c.strip() else " " for c in cells]
                    new_line = "|" + "|".join(parts) + "|"
                    new_lines.append(new_line)
                    updated_count += 1

                # Định dạng bảng 4 cột: | STT | Bài Làm Của Bạn | Kết Quả Tự Check | Ghi Chú |
                elif len(cells) == 4:
                    cells[0] = f"**{q_num}**"
                    if user_ans:
                        cells[1] = f"`{user_ans}`"
                    
                    if is_corr is True:
                        cells[2] = "✅"
                    elif is_corr is False:
                        cells[2] = "❌"
                    else:
                        cells[2] = "[x]" if user_ans else "[ ]"

                    if note:
                        cells[3] = note

                    parts = [f" {c.strip()} " if c.strip() else " " for c in cells]
                    new_line = "|" + "|".join(parts) + "|"
                    new_lines.append(new_line)
                    updated_count += 1
                else:
                    new_lines.append(line)

            if updated_count > 0:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(new_lines) + "\n")
                logger.info(f"[MARKDOWN UPDATER] Đã cập nhật thành công {updated_count} câu vào file: {file_path}")
                return True
            else:
                logger.info(f"[MARKDOWN UPDATER] Không tìm thấy dòng câu hỏi nào cần cập nhật trong {file_path}")
                return False

        except Exception as e:
            logger.error(f"[MARKDOWN UPDATER] Lỗi khi cập nhật bảng đối soát file {file_path}: {e}", exc_info=True)
            return False

    @classmethod
    def update_writing_note(
        cls,
        file_path: str,
        raw_text: str,
        feedback: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> bool:
        """
        Cập nhật bài viết Writing của người học và phản hồi AI vào file Markdown,
        bảo toàn cấu trúc phân tách rõ ràng độc lập giữa Task 1 và Task 2:
        - Task 1: Workspace -> Bài làm thực tế Task 1 -> Chẩn đoán AI Task 1
        - Task 2: Workspace -> Bài làm thực tế Task 2 -> Chẩn đoán AI Task 2
        """
        if not os.path.isfile(file_path):
            logger.warning(f"[MARKDOWN UPDATER] Không tìm thấy file: {file_path}")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            words = len(raw_text.strip().split())

            # 1. Xác định task_num (1 hoặc 2)
            task_num = 1
            if task_id:
                tid_lower = str(task_id).lower()
                if "2" in tid_lower:
                    task_num = 2
                elif "1" in tid_lower:
                    task_num = 1
            else:
                lower_text = raw_text.lower()
                if "task 2" in lower_text or "opinion" in lower_text or "agree or disagree" in lower_text:
                    task_num = 2

            # 2. Chuẩn hóa khối bài làm thực tế
            quoted_lines = "\n".join([f"> {line}" if line.strip() else ">" for line in raw_text.strip().splitlines()])
            user_section = (
                f"#### 📝 Bài Làm Thực Tế Task {task_num} (Lưu Trữ Nguyên Bản - {words} từ)\n\n"
                f"> [!NOTE]\n"
                f"> **Trạng thái:** Đã nộp bài và ghi nhận vào hệ thống PKM | **Độ dài:** {words} từ\n"
                f">\n"
                f"{quoted_lines}\n"
            )

            # 3. Tìm các section Level 2 (## ...) để khoanh vùng Task 1 vs Task 2
            h2_matches = list(re.finditer(r"(?m)^##\s+(.+)$", content))
            target_idx = None
            if h2_matches:
                for idx, m in enumerate(h2_matches):
                    title = m.group(1).lower()
                    if task_num == 1 and ("task 1" in title or "phần 1" in title or "line graph" in title):
                        target_idx = idx
                        break
                    elif task_num == 2 and ("task 2" in title or "phần 2" in title or "opinion" in title or "essay" in title):
                        target_idx = idx
                        break

            if target_idx is not None:
                # Đã khoanh vùng chính xác phạm vi của Task!
                start_pos = h2_matches[target_idx].start()
                end_pos = h2_matches[target_idx + 1].start() if target_idx + 1 < len(h2_matches) else len(content)
                sec_text = content[start_pos:end_pos]

                # Pattern tìm mục bài làm thực tế trong section này (Task 1 hoặc Task 2 hoặc Của Bạn)
                user_pat = re.compile(
                    rf"#### 📝 (?:Bài Làm Thực Tế (?:Task {task_num}|Của Bạn)|Bản Phác Thảo Thực Tế)[^\n]*\n.*?(?=\n#### |\n### |\n## |\n---|\Z)",
                    flags=re.DOTALL
                )

                if user_pat.search(sec_text):
                    sec_text = user_pat.sub(user_section.strip(), sec_text, count=1)
                else:
                    # Kiểm tra xem có `### 🔬 ... Task {task_num}` chưa
                    diag_pat = re.compile(rf"(### 🔬 [^\n]*Task {task_num}[^\n]*\n)", flags=re.IGNORECASE)
                    if diag_pat.search(sec_text):
                        sec_text = diag_pat.sub(r"\1\n" + user_section.strip() + "\n\n", sec_text, count=1)
                    else:
                        div_idx = sec_text.rfind("</div>")
                        if div_idx != -1:
                            insert_at = div_idx + len("</div>")
                            sec_text = (
                                sec_text[:insert_at]
                                + f"\n\n---\n\n### 🔬 Phân Tích & Chẩn Đoán Chi Tiết Task {task_num} (Diagnostic Feedback)\n\n"
                                + user_section.strip()
                                + sec_text[insert_at:]
                            )
                        else:
                            sec_text = sec_text.rstrip() + f"\n\n---\n\n{user_section.strip()}\n\n"

                # Cập nhật feedback AI vào section nếu có
                if feedback:
                    fb_pat = re.compile(
                        rf"#### 🔬 Nhận Xét & Phân Tích Chẩn Đoán Task {task_num} Của AI[^\n]*\n.*?(?=\n#### |\n### |\n## |\Z)",
                        flags=re.DOTALL
                    )
                    clean_fb = f"#### 🔬 Nhận Xét & Phân Tích Chẩn Đoán Task {task_num} Của AI\n\n{feedback.strip()}\n"
                    if fb_pat.search(sec_text):
                        sec_text = fb_pat.sub(clean_fb, sec_text, count=1)
                    else:
                        user_match = re.search(
                            rf"#### 📝 Bài Làm Thực Tế Task {task_num}[^\n]*\n.*?(?=\n#### |\n### |\n## |\n---|\Z)",
                            sec_text,
                            flags=re.DOTALL
                        )
                        if user_match:
                            insert_at = user_match.end()
                            sec_text = sec_text[:insert_at] + f"\n\n---\n\n{clean_fb}" + sec_text[insert_at:]
                        else:
                            sec_text = sec_text.rstrip() + f"\n\n---\n\n{clean_fb}\n\n"

                # Ghép lại content
                content = content[:start_pos] + sec_text + content[end_pos:]

            else:
                # Fallback: Không tìm thấy section ## Task 1 hay ## Task 2, cập nhật theo cơ chế generic
                user_pattern = r"#### 📝 Bài Làm Thực Tế[^\n]*\n.*?(?=\n#### |\n### |\n## |\n---|\Z)"
                if re.search(user_pattern, content, flags=re.DOTALL):
                    content = re.sub(user_pattern, user_section.strip(), content, flags=re.DOTALL)
                else:
                    content += f"\n\n---\n\n{user_section}"

                if feedback:
                    feedback_block = (
                        f"### 🔬 Nhận Xét & Phân Tích Chẩn Đoán Task {task_num} Của AI\n\n"
                        f"{feedback.strip()}\n"
                    )
                    fb_pattern = r"### 🔬 Nhận Xét & Phân Tích Chẩn Đoán[^\n]*\n.*?(?=\n### |\n## |\n---|\Z)"
                    if re.search(fb_pattern, content, flags=re.DOTALL):
                        content = re.sub(fb_pattern, feedback_block.strip(), content, flags=re.DOTALL)
                    else:
                        content += f"\n\n---\n\n{feedback_block}"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"[MARKDOWN UPDATER] Đã cập nhật Task {task_num} ({words} từ) vào {file_path}")
            return True

        except Exception as e:
            logger.error(f"[MARKDOWN UPDATER] Lỗi khi cập nhật bài writing vào {file_path}: {e}", exc_info=True)
            return False

markdown_updater = MarkdownNoteUpdater()

