# 🤖 NoteAI.v2 (Local Autonomous PKM) - Gemini Rules & Governance

Tệp này đồng bộ nội dung và ràng buộc với `AGENTS.md`. Toàn bộ các quy tắc dưới đây là **bắt buộc và có hiệu lực xuyên suốt mọi phiên làm việc**:

---

## 1. 🚫 Nguyên Tắc Vàng (Inviolable Rule)

- **TUYỆT ĐỐI KHÔNG tự đoán đáp án, không tự chấm điểm, không tự suy diễn Band Score** khi người học chưa cung cấp bảng đáp án chính thức.
- Luôn ghi nhận trung thực kết quả làm bài của người học vào bảng đối soát.

---

## 2. ⚡ Cấu Trúc Cổng Mạng & An Toàn Phần Cứng

- **PostgreSQL:** Ánh xạ host **`5433`** $\rightarrow$ container `5432` (`noteai_pkm`). Cấm dùng port `5432` (tránh xung đột với CVAT).
- **Qdrant Vector DB:** Host **`6333`** (REST) và **`6334`** (gRPC).
- **FastAPI Backend:** Host **`8000`** (`http://localhost:8000`, docs tại `/docs`).
- **Interactive React SPA:** Host **`5173`** (`http://localhost:5173`).
- **An toàn phần cứng CPU:** RAG Embedding sử dụng `fastembed` (ONNX CPU AVX2/AVX-512), bảo toàn 4GB VRAM của card NVIDIA T1200.
- **LLM Engine:** Cloud API (Google Gemini API) với Structured Output Pydantic v2.

---

## 3. 🗂️ Phân Cấp Tri Thức (Knowledge Graph Hierarchy)

- **SSOT:** Thư mục `content/` là nguồn dữ liệu duy nhất.
- **Quy chuẩn phân cấp:**
  - Macro Node (`index.md`) $\rightarrow$ Hub Tuần (`plans/week-XX/index.md`) $\rightarrow$ Leaf Node (`test-*.md`, `vocab-*.md`).
  - Leaf Node chỉ được trỏ ngược về Hub cha của nó. Không nối tắt về root index.
- **Quy tắc Chu Kỳ Kế Hoạch Tuần (Weekly Calendar Boundary Rule):**
  - Kế hoạch tuần **BẮT BUỘC kết thúc vào ngày Chủ Nhật (CN)** của tuần đó, **TUYỆT ĐỐI KHÔNG kéo dài sang tuần sau**.
  - Nếu bắt đầu giữa tuần (Thứ 4, 14/10), tuần khởi đầu sẽ từ Thứ 4 đến Chủ Nhật (`14/10 – 18/10`). Tuần tiếp theo sẽ bắt đầu từ Thứ 2 đến Chủ Nhật (`19/10 – 25/10`).

---

## 4. 🏷️ YAML Frontmatter Schema

- Bắt buộc: `title`, `tags`, khuyến nghị: `aliases`.
- **Quy tắc Tiêu Đề Ngắn Gọn Theo Ngày Tháng (Concise Plan Execution Date Rule):** Khi tạo các file Markdown theo plan (`plans/week-XX/...`, `test-*.md`, `vocab-*.md`), tiêu đề (`title:`) **BẮT BUỘC chỉ chứa ngày và tháng (`[DD/MM]`), viết ngắn gọn súc tích** (bỏ tiền tố dài, bỏ năm `/YYYY`) để hiển thị trọn vẹn và dễ đọc trên Explorer/Sidebar/Tab:
  - Định dạng bài test / ngày: `[DD/MM] Tên Ngắn Gọn` (ví dụ: `title: "[14/10] Test 1 Listening"`, `title: "[15/10] Test 1 Reading P3"`, `title: "[16/10] Test 1 Writing"`).
  - Định dạng Hub tuần / Sổ từ vựng: `[DD/MM - DD/MM] Tên Ngắn Gọn` (kết thúc vào Chủ Nhật, ví dụ: `title: "[14/10 - 18/10] Kế Hoạch Tuần 1"`, `title: "[14/10 - 18/10] Từ Vựng Tuần 1"`).
- Riêng file từ vựng/ôn tập bắt buộc có `sr-due: "YYYY-MM-DD"`.

---

## 5. 🧠 Động Cơ Trí Nhớ FSRS v4

- Áp dụng mô hình **DSR** (Difficulty, Stability, Retrievability) qua thư viện `fsrs`.
- 4 mức đánh giá: `Again (1)`, `Hard (2)`, `Good (3)`, `Easy (4)`.
- Dữ liệu lưu trong PostgreSQL (`flashcards` & `review_logs`).

---

## 6. 🛡️ Pipeline Kiểm Chứng Hình Thức

- Trước khi commit git, luôn chạy:

  ```bash
  python scripts/run_pipeline.py
  ```

- 4 chặng: YAML & Dead Link $\rightarrow$ Markdownlint $\rightarrow$ FSRS/Anki Sync $\rightarrow$ Quartz Build.
