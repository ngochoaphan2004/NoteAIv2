import pytest
from app.services.rag_engine import rag_engine

def test_markdown_chunking():
    """Kiểm tra việc tách file Markdown theo cấu trúc Heading"""
    sample_markdown = """
# Tiêu Đề Bài Học

Đoạn văn mở đầu giới thiệu về bài học.

## Kỹ Năng Listening

Nghe audio và chú ý các bẫy trọng âm -teen vs -ty.

## Kỹ Năng Reading

Phương pháp Keyword Mapping giúp xác định từ đồng nghĩa trong Passage 3.
"""
    chunks = rag_engine.chunk_markdown(sample_markdown, "sample.md")
    assert len(chunks) >= 2
    headings = [c["heading"] for c in chunks]
    assert any("Listening" in h for h in headings)
    assert any("Reading" in h for h in headings)

def test_cpu_embedding_generation():
    """Kiểm tra mô hình FastEmbed tạo vector embeddings trên CPU"""
    texts = ["Space debris collision avoidance", "Asian urbanization trends"]
    embeddings = list(rag_engine.embedder.embed(texts))

    assert len(embeddings) == 2
    # BAAI/bge-small-en-v1.5 có dimension là 384
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384

def test_qdrant_search_retrieval():
    """Kiểm tra truy vấn tìm kiếm ngữ nghĩa trong Qdrant Vector DB"""
    query = "space junk and collision"
    results = rag_engine.search_similar(query, limit=3)

    assert isinstance(results, list)
    if results:
        top_hit = results[0]
        assert "score" in top_hit
        assert "source_file" in top_hit
        assert "content" in top_hit
        assert top_hit["score"] > 0.0
