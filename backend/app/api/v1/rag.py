import os
import glob
from typing import Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Body
from app.services.rag_engine import rag_engine
from app.core.config import settings

router = APIRouter(prefix="/rag", tags=["Vector RAG Engine"])

@router.post("/query", response_model=List[Dict[str, Any]])
def query_knowledge_base(
    query: str = Query(..., min_length=2, description="Nội dung cần tìm kiếm ngữ nghĩa"),
    limit: int = Query(default=5, ge=1, le=20)
):
    """Truy vấn ngữ nghĩa kho tài liệu qua Qdrant Vector DB"""
    try:
        results = rag_engine.search_similar(query=query, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi truy vấn Vector DB: {e}")

@router.post("/reindex")
def reindex_all_markdown():
    """Lập chỉ mục lại toàn bộ ghi chú Markdown trong content/ vào Qdrant"""
    content_dir = settings.CONTENT_DIR
    all_md_files = glob.glob(os.path.join(content_dir, "**", "*.md"), recursive=True)

    indexed_count = 0
    total_chunks = 0

    for file_path in all_md_files:
        try:
            chunks = rag_engine.index_markdown_file(file_path)
            if chunks > 0:
                indexed_count += 1
                total_chunks += chunks
        except Exception as e:
            continue

    return {
        "status": "success",
        "files_indexed": indexed_count,
        "total_chunks": total_chunks
    }
