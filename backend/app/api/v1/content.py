import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.content import ContentTreeItem, NoteDetailResponse, NoteSaveRequest
from app.services.content_service import content_service

router = APIRouter(prefix="/content", tags=["Content & Garden"])

@router.get("/tree", response_model=List[ContentTreeItem])
def get_content_tree():
    """Lấy cây thư mục tri thức phân cấp cho Sidebar Explorer"""
    return content_service.get_content_tree()

@router.get("/note", response_model=NoteDetailResponse)
def get_note(path: str = Query(..., description="Đường dẫn tương đối tới file ghi chú (ví dụ: plans/week-01/test-1-listening-p3-p4.md)")):
    """Đọc chi tiết nội dung ghi chú Markdown, frontmatter và exam metadata"""
    note = content_service.get_note_by_path(path)
    if not note:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy tài liệu ghi chú tại '{path}'.")
    return note

@router.put("/note")
def save_note(payload: NoteSaveRequest):
    """Cập nhật nội dung tài liệu Markdown (SSOT)"""
    success = content_service.save_note(payload.path, payload.content)
    if not success:
        raise HTTPException(status_code=500, detail="Không thể lưu tài liệu ghi chú.")
    return {"success": True, "path": payload.path}
