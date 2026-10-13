import os
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from fastembed import TextEmbedding
from app.core.config import settings

logger = logging.getLogger("rag_engine")

class RAGEngine:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self._client: Optional[QdrantClient] = None
        self._embedder: Optional[TextEmbedding] = None
        self.embedding_dim = 384  # Dimension của BAAI/bge-small-en-v1.5

    @property
    def embedder(self) -> TextEmbedding:
        if self._embedder is None:
            logger.info("Initializing FastEmbed TextEmbedding (CPU ONNX: BAAI/bge-small-en-v1.5)...")
            self._embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return self._embedder

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(url=settings.QDRANT_URL, timeout=10.0, check_compatibility=False)
        return self._client

    def ensure_collection(self) -> bool:
        """Đảm bảo Collection Qdrant đã được tạo với cấu hình Cosine Distance"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection '{self.collection_name}' with dimension {self.embedding_dim}...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.embedding_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
            return True
        except Exception as e:
            logger.warning(f"Qdrant connection deferred or not ready: {e}")
            return False

    def chunk_markdown(self, content: str, source_file: str) -> List[Dict[str, Any]]:
        """
        Chia nhỏ Markdown theo cấu trúc Heading mà không làm đứt đoạn bảng hay code block.
        """
        chunks: List[Dict[str, Any]] = []
        current_heading = "Giới thiệu chung"
        current_lines: List[str] = []

        lines = content.splitlines()
        for line in lines:
            # Phát hiện Heading 1, 2, 3
            heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
            if heading_match:
                if current_lines:
                    chunk_text = "\n".join(current_lines).strip()
                    if len(chunk_text) > 30:  # Bỏ qua đoạn quá ngắn
                        chunks.append({
                            "content": chunk_text,
                            "heading": current_heading,
                            "source_file": source_file
                        })
                    current_lines = []
                current_heading = heading_match.group(2).strip()
            current_lines.append(line)

        if current_lines:
            chunk_text = "\n".join(current_lines).strip()
            if len(chunk_text) > 30:
                chunks.append({
                    "content": chunk_text,
                    "heading": current_heading,
                    "source_file": source_file
                })

        return chunks

    def index_markdown_file(self, file_path: str) -> int:
        """Đọc và nạp các vector của file Markdown vào Qdrant"""
        if not os.path.exists(file_path):
            return 0
        if not self.ensure_collection():
            return 0

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        rel_path = os.path.relpath(file_path, settings.CONTENT_DIR)
        chunks = self.chunk_markdown(content, rel_path)
        if not chunks:
            return 0

        # Sinh embeddings hàng loạt trên CPU qua FastEmbed
        texts = [f"[{c['heading']}] {c['content']}" for c in chunks]
        embeddings = list(self.embedder.embed(texts))

        points = []
        for i, chunk in enumerate(chunks):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{rel_path}:{i}"))
            points.append(qmodels.PointStruct(
                id=point_id,
                vector=embeddings[i].tolist(),
                payload={
                    "source_file": chunk["source_file"],
                    "heading": chunk["heading"],
                    "content": chunk["content"]
                }
            ))

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Indexed {len(points)} chunks from {rel_path} into Qdrant.")
        return len(points)

    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Truy vấn ngữ nghĩa vector tìm tài liệu học thuật liên quan nhất"""
        if not self.ensure_collection():
            return []

        query_embedding = list(self.embedder.embed([query]))[0].tolist()

        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit
        )

        results = []
        for hit in search_result.points:
            results.append({
                "score": hit.score,
                "source_file": hit.payload.get("source_file"),
                "heading": hit.payload.get("heading"),
                "content": hit.payload.get("content")
            })
        return results

rag_engine = RAGEngine()
