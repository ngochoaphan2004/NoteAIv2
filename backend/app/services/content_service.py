import os
import re
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.content import ContentTreeItem, NoteDetailResponse, ExamConfigMetadata

logger = logging.getLogger("content_service")

class ContentService:
    """
    Dịch vụ quản trị và phân giải nội dung Digital Garden (SSOT Markdown)
    cho Native React SPA Frontend.
    """

    def __init__(self):
        self._tree_cache: Optional[List[ContentTreeItem]] = None
        self._tree_cache_time: float = 0

    @property
    def content_dir(self) -> str:
        return os.path.abspath(settings.CONTENT_DIR)

    def parse_frontmatter(self, text: str) -> tuple[Dict[str, Any], str]:
        """Tách YAML frontmatter và phần nội dung Markdown body"""
        fm_pattern = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
        match = fm_pattern.match(text)
        if match:
            fm_text = match.group(1)
            body = text[match.end():]
            try:
                metadata = yaml.safe_load(fm_text) or {}
                if not isinstance(metadata, dict):
                    metadata = {}
            except Exception as e:
                logger.warning(f"Lỗi parse YAML frontmatter: {e}")
                metadata = {}
            return metadata, body
        return {}, text

    def extract_headings(self, markdown_text: str) -> List[Dict[str, Any]]:
        """Trích xuất cấu trúc Table of Contents từ các tiêu đề Markdown (#, ##, ###)"""
        headings = []
        for line in markdown_text.splitlines():
            m = re.match(r"^(#{1,4})\s+(.+)$", line.strip())
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                # Tạo slug đơn giản cho anchor ID
                clean_id = re.sub(r"[^\w\s-]", "", text).strip().lower()
                clean_id = re.sub(r"\s+", "-", clean_id)
                headings.append({
                    "level": level,
                    "text": text,
                    "id": clean_id
                })
        return headings

    def detect_exam_metadata(self, text: str, frontmatter: Dict[str, Any], path: str) -> ExamConfigMetadata:
        """Tự động phát hiện loại bài thi tương tác trong ghi chú"""
        meta = ExamConfigMetadata()
        lower_path = path.lower()

        # 1. Phát hiện IELTS Answer Sheet (Listening / Reading)
        m_sheet = re.search(
            r'class="[^"]*ielts-sheet-card[^"]*"[^>]*'
            r'(?:data-start-q="(\d+)")?[^>]*'
            r'(?:data-end-q="(\d+)")?[^>]*'
            r'(?:data-timer="(\d+)")?[^>]*'
            r'(?:data-sheet-id="([^"]*)")?',
            text
        )
        if not m_sheet:
            m_sheet = re.search(r'data-sheet-id="([^"]+)"', text)

        if m_sheet or "listening" in lower_path or "reading" in lower_path:
            meta.has_exam = True
            meta.exam_type = "sheet"
            meta.skill = "reading" if "reading" in lower_path else "listening"

            # Parse start_q and end_q
            start_m = re.search(r'data-start-q="(\d+)"', text)
            end_m = re.search(r'data-end-q="(\d+)"', text)
            timer_m = re.search(r'data-timer="(\d+)"', text)
            sheet_m = re.search(r'data-sheet-id="([^"]+)"', text)

            meta.start_q = int(start_m.group(1)) if start_m else (21 if ("p3" in lower_path or "passage 3" in lower_path) else 1)
            meta.end_q = int(end_m.group(1)) if end_m else (40 if meta.start_q > 20 else (20 if "p1-p2" in lower_path else 40))
            meta.timer_minutes = int(timer_m.group(1)) if timer_m else 18
            meta.sheet_id = sheet_m.group(1) if sheet_m else Path(path).stem

        # 2. Phát hiện Writing Workspace
        m_writing = re.search(r'class="[^"]*ielts-writing-card[^"]*"', text)
        if m_writing or "writing" in lower_path:
            meta.has_exam = True
            meta.exam_type = "writing"
            meta.skill = "writing"

            task_m = re.search(r'data-task="([^"]+)"', text)
            target_m = re.search(r'data-target="(\d+)"', text)
            timer_m = re.search(r'data-timer="(\d+)"', text)

            meta.task_id = task_m.group(1) if task_m else ("task-2" if "task2" in lower_path or "task-2" in lower_path else "task-1")
            meta.target_words = int(target_m.group(1)) if target_m else (250 if meta.task_id == "task-2" else 150)
            meta.timer_minutes = int(timer_m.group(1)) if timer_m else (40 if meta.task_id == "task-2" else 20)

        # 3. Phát hiện Speaking Session
        if "speaking" in lower_path:
            meta.has_exam = True
            meta.exam_type = "speaking"
            meta.skill = "speaking"
            meta.timer_minutes = 15

        return meta

    def get_content_tree(self) -> List[ContentTreeItem]:
        """Tạo cây cấu trúc phân cấp toàn bộ ghi chú trong content/ cho Sidebar Explorer"""
        base_dir = self.content_dir
        if not os.path.exists(base_dir):
            return []

        tree: List[ContentTreeItem] = []

        # 1. Nhóm Kế Hoạch Học Tập (plans/)
        plans_dir = os.path.join(base_dir, "plans")
        if os.path.exists(plans_dir):
            plans_group = ContentTreeItem(
                id="group_plans",
                title="Kế Hoạch Học Tập",
                slug="plans",
                path="plans",
                type="folder",
                icon="Calendar",
                order=1,
                children=[]
            )

            # Quét từng tuần week-XX
            week_folders = sorted(
                [d for d in os.listdir(plans_dir) if os.path.isdir(os.path.join(plans_dir, d)) and d.startswith("week-")],
                key=lambda x: x
            )

            for wf in week_folders:
                w_path = os.path.join(plans_dir, wf)
                w_index = os.path.join(w_path, "index.md")
                w_title = f"Tuần {wf.replace('week-', '')}"
                if os.path.exists(w_index):
                    try:
                        with open(w_index, "r", encoding="utf-8") as f:
                            fm, _ = self.parse_frontmatter(f.read())
                            if fm.get("title"):
                                w_title = fm["title"]
                    except Exception:
                        pass

                week_node = ContentTreeItem(
                    id=f"plan_{wf}",
                    title=w_title,
                    slug=f"plans/{wf}",
                    path=f"plans/{wf}/index.md",
                    type="folder",
                    icon="Folder",
                    children=[]
                )

                # Quét các bài học trong tuần (loại trừ index.md vì đã gắn trực tiếp vào node kế hoạch tuần)
                raw_sub_files = [f for f in os.listdir(w_path) if f.endswith(".md") and f != "index.md"]

                def get_file_sort_key(f_name: str) -> tuple:
                    f_lower = f_name.lower()
                    # 1. Các file sổ từ vựng và review luôn chuyển về cuối danh sách
                    if "vocab" in f_lower:
                        return (2, 10, f_name)
                    if "review" in f_lower:
                        return (2, 20, f_name)

                    # 2. Đọc frontmatter để lấy ngày [DD/MM] trong title
                    t_val = f_name
                    try:
                        with open(os.path.join(w_path, f_name), "r", encoding="utf-8") as f_in:
                            f_fm, _ = self.parse_frontmatter(f_in.read())
                            t_val = f_fm.get("title", f_name)
                    except Exception:
                        pass

                    m_date = re.search(r"\[(\d{1,2})/(\d{1,2})\]", t_val)
                    if m_date:
                        d_val, m_val = int(m_date.group(1)), int(m_date.group(2))
                        return (1, m_val * 100 + d_val, f_name)

                    # 3. Fallback theo thứ tự kỹ năng
                    for idx_sk, sk_name in enumerate(["listening", "reading", "writing", "speaking"]):
                        if sk_name in f_lower:
                            return (1, (idx_sk + 1) * 10, f_name)
                    return (1, 99, f_name)

                sub_files = sorted(raw_sub_files, key=get_file_sort_key)
                for sf in sub_files:
                    sf_path = os.path.join(w_path, sf)
                    sf_title = sf.replace(".md", "")
                    sf_tags = []
                    try:
                        with open(sf_path, "r", encoding="utf-8") as f:
                            fm, _ = self.parse_frontmatter(f.read())
                            sf_title = fm.get("title", sf_title)
                            sf_tags = fm.get("tags", [])
                    except Exception:
                        pass

                    # Chọn icon phù hợp
                    sf_icon = "FileText"
                    if "listening" in sf:
                        sf_icon = "Headphones"
                    elif "reading" in sf:
                        sf_icon = "BookOpen"
                    elif "writing" in sf:
                        sf_icon = "Edit3"
                    elif "speaking" in sf:
                        sf_icon = "Mic"
                    elif "vocab" in sf:
                        sf_icon = "Layers"

                    week_node.children.append(ContentTreeItem(
                        id=f"note_{wf}_{sf.replace('.md', '')}",
                        title=sf_title,
                        slug=f"plans/{wf}/{sf.replace('.md', '')}",
                        path=f"plans/{wf}/{sf}",
                        type="note",
                        tags=sf_tags if isinstance(sf_tags, list) else [sf_tags],
                        icon=sf_icon
                    ))

                plans_group.children.append(week_node)

            tree.append(plans_group)

        # 2. Nhóm Lộ Trình & Ngữ Pháp & Tài Nguyên
        root_notes = sorted([f for f in os.listdir(base_dir) if f.endswith(".md") and f != "index.md"])
        if root_notes:
            res_group = ContentTreeItem(
                id="group_resources",
                title="Tài Nguyên & Định Hướng",
                slug="resources",
                path="resources",
                type="folder",
                icon="Compass",
                order=2,
                children=[]
            )
            for rf in root_notes:
                rf_path = os.path.join(base_dir, rf)
                rf_title = rf.replace(".md", "")
                rf_tags = []
                try:
                    with open(rf_path, "r", encoding="utf-8") as f:
                        fm, _ = self.parse_frontmatter(f.read())
                        rf_title = fm.get("title", rf_title)
                        rf_tags = fm.get("tags", [])
                except Exception:
                    pass

                rf_icon = "Sparkles" if "roadmap" in rf else ("BookOpen" if "grammar" in rf else "FileText")
                res_group.children.append(ContentTreeItem(
                    id=f"root_note_{rf.replace('.md', '')}",
                    title=rf_title,
                    slug=rf.replace(".md", ""),
                    path=rf,
                    type="note",
                    tags=rf_tags if isinstance(rf_tags, list) else [rf_tags],
                    icon=rf_icon
                ))

            tree.append(res_group)

        return tree

    def get_note_by_path(self, rel_path: str) -> Optional[NoteDetailResponse]:
        """Đọc và phân giải một file Markdown theo đường dẫn tương đối trong content/"""
        clean_path = rel_path.strip().replace("\\", "/").lstrip("/")
        if clean_path.startswith("content/"):
            clean_path = clean_path[len("content/"):].lstrip("/")
        if not clean_path.endswith(".md"):
            clean_path += ".md"

        full_path = os.path.join(self.content_dir, clean_path)
        if not os.path.isfile(full_path):
            # Thử tìm file index.md trong thư mục tương ứng (ví dụ: plans/week-01 -> plans/week-01/index.md)
            dir_index = os.path.join(self.content_dir, clean_path.replace(".md", ""), "index.md")
            if os.path.isfile(dir_index):
                full_path = dir_index
                clean_path = os.path.relpath(dir_index, self.content_dir).replace("\\", "/")
            else:
                # Thử tìm theo basename
                base_name = os.path.basename(clean_path)
                found = None
                for root, _, files in os.walk(self.content_dir):
                    if base_name in files:
                        found = os.path.join(root, base_name)
                        clean_path = os.path.relpath(found, self.content_dir).replace("\\", "/")
                        break
                if found:
                    full_path = found
                else:
                    logger.warning(f"Không tìm thấy file ghi chú: {rel_path} (full: {full_path})")
                    return None

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            frontmatter, body = self.parse_frontmatter(raw_text)
            title = frontmatter.get("title") or Path(clean_path).stem
            slug = clean_path.replace(".md", "")
            if slug.endswith("/index"):
                slug = slug[:-6]

            exam_metadata = self.detect_exam_metadata(raw_text, frontmatter, clean_path)
            headings = self.extract_headings(raw_text)

            return NoteDetailResponse(
                title=title,
                slug=slug,
                path=clean_path,
                frontmatter=frontmatter,
                raw_content=raw_text,
                exam_metadata=exam_metadata,
                headings=headings
            )
        except Exception as e:
            logger.error(f"Lỗi khi đọc file ghi chú {full_path}: {e}", exc_info=True)
            return None

    def save_note(self, rel_path: str, content: str) -> bool:
        """Lưu nội dung cập nhật vào file ghi chú Markdown (SSOT)"""
        clean_path = rel_path.strip().replace("\\", "/").lstrip("/")
        if clean_path.startswith("content/"):
            clean_path = clean_path[len("content/"):].lstrip("/")
        if not clean_path.endswith(".md"):
            clean_path += ".md"

        full_path = os.path.join(self.content_dir, clean_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.invalidate_cache()
            return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu file ghi chú {full_path}: {e}", exc_info=True)
            return False

content_service = ContentService()
