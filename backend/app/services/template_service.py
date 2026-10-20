import os
import re
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger("template_service")

class TemplateService:
    """
    Centralized Template Engine & Governance Validator for NoteAI.v2.
    Đảm bảo 100% các file Markdown sinh ra bởi Trợ lý AI và Cronjob / Planning Agent
    đều tuân thủ nghiêm ngặt hệ thống mẫu chuẩn tại thư mục `templates/`.
    """

    TEMPLATES = {
        "weekly_plan": "template-weekly-plan.md",
        "listening_session": "template-listening-session.md",
        "reading_session": "template-reading-session.md",
        "writing_session": "template-writing-session.md",
        "speaking_session": "template-speaking-session.md",
        "vocab_week": "template-vocab-week.md",
        "review_week": "template-review-week.md",
    }

    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or settings.TEMPLATE_DIR
        self._cache: Dict[str, str] = {}

    def get_template_path(self, template_key_or_filename: str) -> str:
        """Lấy đường dẫn tuyệt đối của file template."""
        filename = self.TEMPLATES.get(template_key_or_filename, template_key_or_filename)
        return os.path.join(self.template_dir, filename)

    def load_template(self, template_key_or_filename: str) -> str:
        """Đọc nội dung template từ đĩa (có bộ nhớ đệm cache)."""
        filename = self.TEMPLATES.get(template_key_or_filename, template_key_or_filename)
        if filename in self._cache:
            return self._cache[filename]

        path = os.path.join(self.template_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template không tồn tại: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self._cache[filename] = content
        return content

    def render(self, template_key_or_filename: str, context: Dict[str, Any]) -> str:
        """
        Điền các biến context vào template chuẩn.
        Mọi placeholder dạng {{KEY}} sẽ được thay thế bằng giá trị tương ứng.
        """
        raw = self.load_template(template_key_or_filename)
        
        def replace_match(match):
            key = match.group(1).strip()
            if key in context:
                val = context[key]
                return str(val) if val is not None else ""
            return match.group(0)

        # Thay thế các biến {{VAR}}
        rendered = re.sub(r"\{\{([A-Za-z0-9_]+)\}\}", replace_match, raw)
        
        # Kiểm tra còn sót biến chưa render không
        unresolved = re.findall(r"\{\{([A-Za-z0-9_]+)\}\}", rendered)
        if unresolved:
            logger.warning(
                f"[TemplateService] Template '{template_key_or_filename}' còn các biến chưa render: {set(unresolved)}"
            )

        return rendered

    def validate_markdown(self, content: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Kiểm tra hình thức và quy chuẩn của ghi chú Markdown đối chiếu với template chuẩn.
        Bao gồm:
        - Frontmatter YAML hợp lệ.
        - Quy tắc tiêu đề theo ngày tháng [DD/MM] hoặc [DD/MM - DD/MM].
        - Thẻ tương tác theo kỹ năng (Listening/Reading có grid answers, Writing có writing card, Speaking có workspace).
        - Liên kết 2 chiều về Hub tuần cha.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Kiểm tra Frontmatter YAML
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not frontmatter_match:
            errors.append("Thiếu khối YAML Frontmatter mở đầu (bắt đầu và kết thúc bằng ---)")
            fm_data = {}
        else:
            fm_text = frontmatter_match.group(1)
            try:
                fm_data = yaml.safe_load(fm_text) or {}
            except Exception as e:
                errors.append(f"YAML Frontmatter bị lỗi cú pháp: {e}")
                fm_data = {}

        # 2. Kiểm tra title
        title = fm_data.get("title", "")
        if not title:
            errors.append("Frontmatter thiếu trường 'title'")
        else:
            # Kiểm tra quy tắc tiêu đề ngắn gọn theo ngày tháng: [DD/MM] hoặc [DD/MM - DD/MM]
            date_prefix_pattern = r"^\[\d{1,2}/\d{1,2}(\s*[-–]\s*\d{1,2}/\d{1,2})?\]"
            if not re.search(date_prefix_pattern, title):
                warnings.append(f"Tiêu đề '{title}' chưa có tiền tố ngày thực hiện dạng [DD/MM] hoặc [DD/MM - DD/MM]")

        # 3. Kiểm tra tags
        tags = fm_data.get("tags", [])
        if not tags or not isinstance(tags, list):
            errors.append("Frontmatter 'tags' phải là một danh sách có ít nhất 1 thẻ")

        # 4. Kiểm tra thành phần tương tác theo từng loại template
        if expected_type in ("listening_session", "reading_session") or "ielts-sheet-card" in content:
            if '<div class="ielts-grid-answers"></div>' not in content:
                errors.append("Listening/Reading note BẮT BUỘC chứa '<div class=\"ielts-grid-answers\"></div>' để engine JS sinh ô nhập")
            if 'data-sheet-id=' not in content:
                warnings.append("ielts-sheet-card thiếu thuộc tính data-sheet-id")
            if 'ielts-timer-widget' not in content:
                warnings.append("Thiếu widget đếm ngược thời gian làm bài (ielts-timer-widget)")

        if expected_type == "writing_session" or "ielts-writing-card" in content:
            if 'class="ielts-writing-card"' not in content:
                errors.append("Writing note BẮT BUỘC chứa thẻ container '<div class=\"ielts-writing-card\"...'")

        if expected_type == "speaking_session" or "ielts-speaking-workspace" in content:
            if 'class="ielts-speaking-workspace"' not in content:
                errors.append("Speaking note BẮT BUỘC chứa container '<div class=\"ielts-speaking-workspace\"...'")

        if expected_type == "vocab_week" or "vocab" in tags:
            if "sr-due" not in fm_data:
                errors.append("Sổ từ vựng tuần BẮT BUỘC có trường 'sr-due: YYYY-MM-DD' trong frontmatter")
            if "| Từ Vựng (Front) |" not in content and "| Từ vựng (Front) |" not in content:
                warnings.append("Sổ từ vựng chưa có bảng từ vựng Markdown chuẩn cho bộ trích xuất FSRS")

        # 5. Kiểm tra liên kết phân cấp ngược về Hub tuần cha đối với Leaf Node
        if expected_type in ("listening_session", "reading_session", "writing_session", "speaking_session", "vocab_week", "review_week"):
            if not re.search(r"\[\[plans/week-\d{2}/[^\]]*\]\]", content):
                errors.append("Leaf Node BẮT BUỘC phải có liên kết ngược về Hub tuần cha [[plans/week-XX/...]]")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "frontmatter": fm_data
        }

template_service = TemplateService()
