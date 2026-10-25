from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ExamConfigMetadata(BaseModel):
    """Metadata cấu hình bài thi bóc tách từ Frontmatter hoặc thẻ tương tác"""
    has_exam: bool = False
    exam_type: Optional[str] = Field(default=None, description="sheet | writing | speaking")
    sheet_id: Optional[str] = None
    task_id: Optional[str] = None
    skill: Optional[str] = None
    start_q: int = 1
    end_q: int = 40
    timer_minutes: int = 30
    target_words: Optional[int] = None

class ContentTreeItem(BaseModel):
    """Mục trong cây phân cấp thư mục Digital Garden"""
    id: str
    title: str
    slug: str
    path: str
    type: str = Field(..., description="'folder' | 'note'")
    tags: List[str] = Field(default_factory=list)
    icon: Optional[str] = None
    order: int = 0
    children: List["ContentTreeItem"] = Field(default_factory=list)

ContentTreeItem.model_rebuild()

class NoteDetailResponse(BaseModel):
    """Chi tiết nội dung bài học Markdown được trả về cho React SPA"""
    title: str
    slug: str
    path: str
    frontmatter: Dict[str, Any] = Field(default_factory=dict)
    raw_content: str
    exam_metadata: ExamConfigMetadata = Field(default_factory=ExamConfigMetadata)
    headings: List[Dict[str, Any]] = Field(default_factory=list, description="Table of contents [{level, text, id}]")

class NoteSaveRequest(BaseModel):
    """Payload khi lưu hoặc chỉnh sửa file Markdown từ giao diện"""
    path: str
    content: str
