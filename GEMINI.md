# 🤖 NoteAI.v2 (Local Autonomous PKM) - Gemini Rules & Governance

Tệp này đồng bộ nội dung và ràng buộc với `AGENTS.md`. Toàn bộ các quy tắc dưới đây là **bắt buộc và có hiệu lực xuyên suốt mọi phiên làm việc**:

---

## 1. 🚫 Nguyên Tắc Vàng (Inviolable Rule)

* **TUYỆT ĐỐI KHÔNG tự đoán đáp án, không tự chấm điểm, không tự suy diễn Band Score** khi người học chưa cung cấp bảng đáp án chính thức.
* Luôn ghi nhận trung thực kết quả làm bài của người học vào bảng đối soát.

---

## 2. ⚡ Cấu Trúc Cổng Mạng & An Toàn Phần Cứng

* **PostgreSQL:** Ánh xạ host **`5433`** $\rightarrow$ container `5432` (`noteai_pkm`). Cấm dùng port `5432` (tránh xung đột với CVAT).
* **Qdrant Vector DB:** Host **`6333`** (REST) và **`6334`** (gRPC).
* **FastAPI Backend:** Host **`8000`** (`http://localhost:8000`, docs tại `/docs`).
* **Interactive React SPA:** Host **`5173`** (`http://localhost:5173`).
* **An toàn phần cứng CPU:** RAG Embedding sử dụng `fastembed` (ONNX CPU AVX2/AVX-512), bảo toàn 4GB VRAM của card NVIDIA T1200.
* **LLM Engine:** Cloud API (Google Gemini API) với Structured Output Pydantic v2.

---

## 3. 🗂️ Phân Cấp Tri Thức (Knowledge Graph Hierarchy)

* **SSOT:** Thư mục `content/` là nguồn dữ liệu duy nhất.
* **Quy chuẩn phân cấp:**
  * Macro Node (`index.md`) $\rightarrow$ Hub Tuần (`plans/week-XX/index.md`) $\rightarrow$ Leaf Node (`test-*.md`, `vocab-*.md`).
  * Leaf Node chỉ được trỏ ngược về Hub cha của nó. Không nối tắt về root index.

---

## 4. 🏷️ YAML Frontmatter Schema

* Bắt buộc: `title`, `tags`, khuyến nghị: `aliases`.
* Riêng file từ vựng/ôn tập bắt buộc có `sr-due: "YYYY-MM-DD"`.

---

## 5. 🧠 Động Cơ Trí Nhớ FSRS v4

* Áp dụng mô hình **DSR** (Difficulty, Stability, Retrievability) qua thư viện `fsrs`.
* 4 mức đánh giá: `Again (1)`, `Hard (2)`, `Good (3)`, `Easy (4)`.
* Dữ liệu lưu trong PostgreSQL (`flashcards` & `review_logs`).

---

## 6. 🛡️ Pipeline Kiểm Chứng Hình Thức

* Trước khi commit git, luôn chạy:

  ```bash
  python scripts/run_pipeline.py
  ```

* 4 chặng: YAML & Dead Link $\rightarrow$ Markdownlint $\rightarrow$ FSRS/Anki Sync $\rightarrow$ Quartz Build.
