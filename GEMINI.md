# 🤖 NoteAI.v2 (Local Autonomous PKM) - Gemini Rules & Governance

Tệp này đồng bộ nội dung và ràng buộc với `AGENTS.md`. Toàn bộ các quy tắc dưới đây là **bắt buộc và có hiệu lực xuyên suốt mọi phiên làm việc**:

---

## 1. 🎯 Luồng Chấm Điểm & Đối Soát Trực Tiếp Với Kho Đáp Án Chuẩn

- Thay vì yêu cầu người dùng nhập tay đáp án qua tab "Luyện thi & Chấm bài", hệ thống **sử dụng trực tiếp kho đáp án chính thức Cambridge 18 có sẵn trong `data/`** để chấm điểm bài làm trực tiếp.
- Người học làm bài và nộp trực tiếp qua bảng làm bài tương tác trong Daily Session (React SPA). AI tự động tra cứu đáp án chuẩn trong `data/`, chấm điểm, ước lượng Band Score và phân tích bẫy lỗi sai.
- Tuyệt đối không tự suy diễn hoặc bịa đáp án ngoài phạm vi dữ liệu đề chuẩn Cambridge.

---

## 2. ⚡ Cấu Trúc Cổng Mạng Khóa 127.0.0.1 & Cloudflare Tunnel

- **Khóa chặt cổng trên 127.0.0.1:** Ngăn chặn truy cập trực tiếp từ IP public, toàn bộ lưu lượng công cộng đi qua **Cloudflare Tunnel (`cloudflared`)**.
  - **PostgreSQL:** Ánh xạ host **`127.0.0.1:5433`** $ightarrow$ container `5432` (`noteai_pkm`). Cấm dùng port `5432` (tránh xung đột với CVAT).
  - **Qdrant Vector DB:** Host **`127.0.0.1:6333`** (REST) và **`127.0.0.1:6334`** (gRPC).
  - **FastAPI Backend:** Host **`127.0.0.1:8000`** (`http://127.0.0.1:8000`, docs tại `/docs`).
  - **Interactive React SPA:** Host **`127.0.0.1:5173`** (`http://127.0.0.1:5173`).
- **Loại bỏ Nginx:** Không sử dụng Nginx, chuyển hoàn toàn sang Cloudflare Tunnel.
- **Xác thực đăng nhập:** Trang Login bảo vệ ứng dụng (mặc định: `admin` / `noteai2026`).
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
  python scripts/_py_/run_pipeline.py
  # (hoặc: python scripts/run_pipeline.py)
  ```

- 4 chặng: YAML & Dead Link $\rightarrow$ Markdownlint $\rightarrow$ FSRS/Anki Sync $\rightarrow$ React SPA Build.

---

## 7. 📐 Quy Chuẩn Template Bắt Buộc Toàn Dự Án (Mandatory Project Templates)

- **Nguyên tắc cốt lõi:** Cả **Trợ lý AI (Antigravity)** và **AI Cronjob / Autonomous Planning Agent** BẮT BUỘC tuân thủ 100% hệ thống 7 mẫu chuẩn tại thư mục `templates/` (`template-weekly-plan.md`, `template-listening-session.md`, `template-reading-session.md`, `template-writing-session.md`, `template-speaking-session.md`, `template-vocab-week.md`, `template-review-week.md`).
- **Ràng buộc tương tác bất biến:**
  - Listening & Reading BẮT BUỘC chứa container `.ielts-sheet-card` cùng `<div class="ielts-grid-answers"></div>` để React component `IeltsAnswerSheet` tự động render bảng điền đáp án, bộ đếm giờ và lưu trữ bền vững LocalStorage.
  - Sổ từ vựng tuần BẮT BUỘC có `sr-due: "YYYY-MM-DD"` và bảng từ vựng đúng định dạng để FSRS đồng bộ.
  - Mọi bài con (Leaf Node) BẮT BUỘC chỉ liên kết ngược về Hub tuần cha `[[plans/week-XX/|...]]`.

