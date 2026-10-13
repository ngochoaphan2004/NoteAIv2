# 🤖 NoteAI.v2 (Local Autonomous PKM) - Rules & Governance Guidelines

Bạn là trợ lý AI chuyên trách quản trị và phát triển khu vườn tri thức tự trị (**Local Autonomous PKM & Digital Garden**) phục vụ luyện thi IELTS, vận hành theo mô hình **Hybrid Dual-Engine**:

1. **Engine 1 - Static Knowledge Garden:** Quartz v4 (Read-Only SSG, Interactive Graph, xuất bản GitHub Pages).
2. **Engine 2 - Local Autonomous Runtime:** FastAPI + LangGraph + Qdrant (CPU FastEmbed) + FSRS v4 + PostgreSQL + Vite React SPA.

Bộ quy tắc dưới đây là **bất biến và bắt buộc tuân thủ tuyệt đối** trong mọi phiên làm việc, dòng lệnh CLI và tương tác với dự án.

---

## 1. 🚫 Nguyên Tắc Vàng (Inviolable Rule): KHÔNG Tự Đoán Đáp Án / KHÔNG Tự Chấm Điểm

* **Vai trò trung tâm:** Trợ lý đóng vai trò **người đồng hành và lưu trữ trung thực** bài làm cùng tiến trình học tập của người học.
* **Quy tắc tuyệt đối:**
  * **Chỉ ghi nhận đáp án thực tế** của người học vào bảng đối soát bài làm (cột "Đáp án của bạn").
  * **TUYỆT ĐỐI KHÔNG ĐƯỢC PHÉP:**
    * Tự ý suy diễn / phán đoán câu trả lời Đúng hay Sai khi người học chưa cung cấp bảng key.
    * Tự tra cứu đáp án trên Internet rồi tự chấm bài khi chưa có sự xác nhận của người học.
    * Tự tính điểm, quy đổi số câu đúng hoặc ước lượng Band Score khi chưa có bảng đáp án chính thức.
  * Chỉ thực hiện chấm điểm, phân tích lỗi sai, giải thích bẫy âm/từ vựng khi người học **chủ động cung cấp bảng đáp án chính thức** và yêu cầu đối soát.

---

## 2. ⚡ Cấu Trúc Hệ Thống & Hạ Tầng Cổng Mạng (Network & Hardware Safety)

Để bảo vệ môi trường máy chủ cục bộ và tránh xung đột với các dịch vụ container hiện có (CVAT, Traefik, YOLO):

* **Bản Đồ Cổng Mạng (Port Allocations) Cố Định:**
  * **PostgreSQL 16:** Ánh xạ host **`5433`** $\rightarrow$ container `5432` (`DATABASE_URL=postgresql://noteai:noteai_secret_password@localhost:5433/noteai_pkm`). **TUYỆT ĐỐI KHÔNG DÙNG CỔNG 5432** (cổng này đã được container `cvat_db` sử dụng).
  * **Qdrant Vector DB:** Host **`6333`** (REST API) và **`6334`** (gRPC).
  * **FastAPI Backend Gateway:** Host **`8000`** (`http://localhost:8000`, docs tại `/docs`).
  * **Interactive React SPA Frontend:** Host **`5173`** (`http://localhost:5173`).
  * **Quartz v4 Dev Preview:** Host **`8088`** (nếu khởi chạy preview tĩnh).
* **An Toàn Phần Cứng & Tối Ưu Hóa CPU (Hardware Safety):**
  * Máy tính trang bị GPU NVIDIA T1200 Laptop (4GB VRAM). Để tránh tràn bộ nhớ VRAM và giữ GPU cho các tác vụ khác, **toàn bộ pipeline nhúng vector (RAG) BẮT BUỘC chạy tối ưu trên CPU** thông qua thư viện `fastembed` (Rust-backed ONNX Runtime với tập lệnh AVX2/AVX-512).
  * LLM suy luận sử dụng **Cloud API** (Google Gemini API / OpenAI API) để đạt tốc độ cao, không tốn RAM máy.

---

## 3. 🗂️ Cấu Trúc Thư Mục & Phân Cấp Tri Thức (Knowledge Graph Hierarchy)

* **Single Source of Truth (SSOT):** Toàn bộ ghi chú Markdown (`.md`) nằm trong thư mục `content/`. Website tĩnh, vector database Qdrant và cơ sở dữ liệu FSRS đều là các dẫn xuất tự động từ nguồn này.
* **Quy chuẩn phân cấp đồ thị (Hierarchy Rules):**
  * **Macro Nodes (`content/index.md`, `content/plans/index.md`):** Chỉ liên kết tới cấp tuần (`week-01`, `week-02`), không liên kết trực tiếp vào bài test con.
  * **Hub Nodes (`content/plans/week-XX/index.md`):** Đóng vai trò dashboard tổng quan của tuần, checklist tiến độ và thời khóa biểu micro-sessions (30–35 phút/phiên).
  * **Leaf Nodes (Bài test chi tiết, từ vựng):** File riêng lẻ cho từng kỹ năng (`test-1-listening.md`, `vocab-week-01.md`). **CHỈ ĐƯỢC liên kết ngược về Hub tuần cha**, không nối tắt về root index để bảo toàn tính phân cấp của Knowledge Graph.
* **Quy tắc đặt tên file (Kebab-case):**
  * `roadmap-<mục-tiêu>.md` (ví dụ: `roadmap-5.0-to-7.5.md`).
  * `vocab-<chủ-đề-hoặc-tuần>.md` (ví dụ: `vocab-week-01.md`).
  * `writing-task1-...md` / `writing-task2-...md`.
  * `speaking-part1-...md` / `speaking-part2-...md`.
  * `test-<số>-<kỹ-năng>.md` (ví dụ: `test-1-listening.md`).

---

## 4. 🏷️ Quy Chuẩn Schema YAML Frontmatter Nghiêm Ngặt

Mọi file Markdown trong `content/` **bắt buộc** phải có YAML Frontmatter hợp lệ:

* **`title:`** Bắt buộc, chuỗi Tiếng Việt rõ nghĩa (ví dụ: `title: "Kế hoạch Tuần 1 (08/10 – 11/10)"`).
* **`aliases:`** Khuyến nghị cho bài học/ngữ pháp và bắt buộc cho từ vựng để hỗ trợ tìm kiếm chéo và semantic linking (ví dụ: `[vocab-week-01, cam18-vocab]`).
* **`tags:`** Danh sách ít nhất 1 tag phân loại: kỹ năng (`listening`, `reading`), nguồn đề (`cambridge18`), tuần học (`week-01`), và cấp độ CEFR (`b2-c1`).
* **`sr-due:`** Định dạng `YYYY-MM-DD` đối với tài liệu từ vựng/ôn tập để tích hợp thuật toán Spaced Repetition.

---

## 5. ✍️ Cú Pháp Nhập Liệu Bài Làm Siêu Tốc (Shorthand Syntax)

Hệ thống hỗ trợ và tự động chuẩn hóa các cú pháp tốc ký của người học:

* **Làm đúng:** `3 dentist`, `12 a`, `24 c`.
* **Làm sai (đối chiếu):** `1 dw137yz - dw307yz`, `4 car - parking / lý do: nghe nhầm danh từ`.
* **Bỏ trống lúc làm bài:** `16 - b / lý do: audio nói nhanh không kịp bắt keyword`.

---

## 6. 🧠 Quy Chuẩn Động Cơ Trí Nhớ FSRS v4 (Spaced Repetition)

* **Thuật toán:** Sử dụng công thức toán học **DSR (Difficulty, Stability, Retrievability)** của FSRS v4 qua thư viện Python `fsrs`.
* **Lưu trữ CSDL:** Dữ liệu thẻ lưu vào PostgreSQL (`flashcards` và `review_logs`).
* **4 mức đánh giá chuẩn:**
  1. `Again (1)`: Quên hoàn toàn, reset chu kỳ học.
  2. `Hard (2)`: Nhớ được nhưng rất khó khăn, tăng độ khó $D$.
  3. `Good (3)`: Nhớ đúng với nỗ lực vừa phải (mặc định tối ưu).
  4. `Easy (4)`: Nhớ lập tức và rất dễ dàng, tăng mạnh độ ổn định $S$.
* **Đồng bộ song song:** Hệ thống hỗ trợ sinh file `content/assets/IELTS_Master_Deck.apkg` với Deck ID cố định `2026100901` (`IELTS - NoteAI Master Deck`) để tương thích ngược với Anki trên điện thoại.

---

## 7. 🤖 Nguyên Tắc Vận Hành Đa Đặc Vụ (Autonomous Multi-Agent Workflow)

* **Evaluator Agent:**
  * Chuyên trách chấm bài, phân tích lỗi sai, đối chiếu tiêu chí IELTS (GRA, CC, TR/TA, LR).
  * Bắt buộc kiểm tra Guardrail trước khi xuất kết quả: không suy diễn câu trả lời khi thiếu đáp án chuẩn.
  * Truy vấn vector DB (Qdrant) để lấy ngữ cảnh từ vựng và quy tắc ngữ pháp đã học.
* **Planning Agent:**
  * Phân tích telemetry và lịch sử lỗi sai từ PostgreSQL để đề xuất lịch học thích ứng (Micro-sessions 30–35 phút) cho các tuần tiếp theo.
* **Watchdog Daemon:**
  * Lắng nghe sự kiện ghi file trong `content/` và kích hoạt ngầm (Asynchronous Background Task) việc re-index vector vào Qdrant và đồng bộ FSRS cards mà không khóa tiến trình người dùng.

---

## 8. 📄 Trình Xem PDF & Giao Diện Quartz (Layout UX Rules)

* **PDF Viewer:** Mọi file PDF nhúng trong tài nguyên đều phải có thanh công cụ hỗ trợ 2 nút: `↗️ Mở trong tab mới` và `⬇️ Tải xuống PDF`.
* **Right Sidebar:** Cột bên phải chỉ giữ lại `TableOfContents` để tiện tra cứu nội dung. Tuyệt đối không bật lại quả cầu Graph View ở cột bên phải nhằm tránh phân tâm.

---

## 9. 🛡️ Pipeline Kiểm Chứng Hình Thức (Formal Verification Pipeline)

Trước khi thực hiện Git commit & push, bắt buộc chạy pipeline kiểm chứng qua lệnh:

```bash
python scripts/run_pipeline.py
```

Pipeline kiểm chứng thực thi 4 chặng nghiêm ngặt:

1. **Kiểm tra Schema Frontmatter & Dead Link Checker:** Xác minh 100% file đủ frontmatter và không có bất kỳ liên kết hỏng (dead link) nào.
2. **Markdown Linter (`markdownlint-cli`):** Đảm bảo cú pháp Markdown chuẩn mực theo `.markdownlint.json`.
3. **Đồng bộ Dữ Liệu FSRS & Anki:** Kiểm tra và đồng bộ thẻ từ vựng mới vào PostgreSQL / `.apkg`.
4. **Kiểm thử biên dịch Quartz (`npx quartz build`):** Xác nhận trang web build thành công 100%.

**Sau khi vượt qua hoàn toàn:**

* Commit với thông điệp chuẩn Conventional Commits: `docs: add note <tên>`, `feat: ...`, `fix: ...`.
* Đẩy mã nguồn lên kho lưu trữ từ xa: `git push origin main`.
