import os
import glob
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel, Field
from app.services.rag_engine import rag_engine
from app.core.config import settings

router = APIRouter(prefix="/rag", tags=["Vector RAG Engine"])

class ContextSource(BaseModel):
    source_file: str = Field(description="Đường dẫn file nguồn Markdown")
    heading: str = Field(description="Tiêu đề mục tương ứng")
    content: str = Field(description="Đoạn văn bản trích lục")
    score: float = Field(description="Điểm tương đồng Cosine (0.0 -> 1.0)")

class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Câu hỏi cần giải đáp dựa trên kho tài liệu")
    top_k: int = Field(default=4, ge=1, le=10, description="Số lượng ngữ cảnh trích xuất tương đồng nhất")

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[ContextSource]
    model_used: Optional[str] = None

@router.post("/ask", response_model=AskResponse)
def ask_knowledge_base(req: AskRequest):
    """
    Quy trình Hỏi Đáp Tri Thức (Grounded RAG Q&A):
    1. Câu hỏi qua mô hình FastEmbed CPU (BAAI/bge-small-en-v1.5) -> Vector Embedding
    2. Ma trận cấu trúc ngữ nghĩa -> Tính toán độ tương đồng Cosine trong Qdrant -> Trích xuất Top K
    3. Ghép Top K ngữ cảnh + Câu hỏi -> Đưa qua mô hình AI (LLM) với prompt nghiêm ngặt:
       'Chỉ sử dụng ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi. Nếu thông tin không có trong ngữ cảnh, hãy nói không biết.'
    4. Trả về đáp án chính xác cùng các trích dẫn tài liệu gốc.
    """
    try:
        # Bước 1 & 2: Tìm kiếm ngữ cảnh tương đồng nhất từ Qdrant
        contexts = rag_engine.search_similar(query=req.question, limit=req.top_k)

        if not contexts:
            return AskResponse(
                question=req.question,
                answer="Không tìm thấy tài liệu hay ngữ cảnh nào liên quan trong kho tri thức để trả lời câu hỏi này.",
                sources=[],
                model_used=None
            )

        # Bước 3: Đóng gói ngữ cảnh
        context_blocks = []
        for idx, item in enumerate(contexts, 1):
            src = item.get("source_file") or "Tài liệu"
            heading = item.get("heading") or "Nội dung"
            content = (item.get("content") or "").strip()
            score = round(float(item.get("score", 0.0)), 4)
            context_blocks.append(
                f"[Tài liệu {idx} - Nguồn: {src} > {heading} (Độ tương đồng: {score * 100:.1f}%)]\n{content}"
            )

        full_context = "\n\n".join(context_blocks)

        # Prompt chuẩn theo yêu cầu:
        # "Chỉ sử dụng ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi. Nếu thông tin không có trong ngữ cảnh, hãy nói không biết."
        system_message = (
            "Bạn là trợ lý học tập IELTS NoteAI.v2. "
            "Chỉ sử dụng ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi. "
            "Nếu thông tin không có trong ngữ cảnh, hãy nói không biết."
        )

        user_prompt = (
            f"NGỮ CẢNH ĐƯỢC CUNG CẤP:\n\n{full_context}\n\n"
            f"CÂU HỎI: {req.question}\n\n"
            f"YÊU CẦU QUAN TRỌNG: Chỉ sử dụng ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi. "
            f"Nếu thông tin không có trong ngữ cảnh, hãy nói không biết. "
            f"Trả lời rõ ràng, chính xác, súc tích bằng Tiếng Việt (hoặc kèm thuật ngữ Tiếng Anh nếu là đề thi IELTS/từ vựng)."
        )

        # Bước 4: Gọi mô hình AI với cơ chế Fallback tự động
        from app.services.llm_service import llm_service
        answer = llm_service.generate_text(prompt=user_prompt, system_message=system_message)

        sources = [
            ContextSource(
                source_file=c.get("source_file") or "",
                heading=c.get("heading") or "",
                content=c.get("content") or "",
                score=round(float(c.get("score", 0.0)), 4)
            )
            for c in contexts
        ]

        return AskResponse(
            question=req.question,
            answer=answer,
            sources=sources,
            model_used=llm_service.last_used_model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý hỏi đáp RAG: {e}")

@router.post("/query", response_model=List[Dict[str, Any]])
def query_knowledge_base(
    query: str = Query(..., min_length=2, description="Nội dung cần tìm kiếm ngữ nghĩa"),
    limit: int = Query(default=5, ge=1, le=20)
):
    """Truy vấn ngữ nghĩa kho tài liệu thô qua Qdrant Vector DB"""
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
