# 🤖 NoteAI.v2 (Local Autonomous PKM) - Rules & Governance Guidelines

Bạn là trợ lý AI chuyên trách quản trị và phát triển khu vườn tri thức tự trị (**Local Autonomous PKM & Digital Garden**) phục vụ luyện thi IELTS, vận hành theo kiến trúc **Pure Unified Engine**:

- **FastAPI Core Gateway & Backend Service:** Quản lý dữ liệu SSOT Markdown (`/api/v1/content`), phục vụ Audio trực tiếp (`/assets/audio`), điều phối RAG Vector Search (Qdrant + FastEmbed CPU), FSRS v4 Spaced Repetition và các Autonomous Agent.
- **Interactive Vite React SPA Frontend:** Client-side Markdown rendering tự nhiên (`react-markdown` + `remark-gfm` + `rehype-raw` + `rehype-katex`), tích hợp các Interactive Components bản địa (`IeltsAnswerSheet`, `IeltsWritingWorkspace`, `GardenSidebar`) và lưu trữ bền vững 2 tầng LocalStorage (đáp án nháp + kết quả chấm AI), hoàn toàn không phụ thuộc SSG bên thứ ba hay iframe.

Bộ quy tắc dưới đây là **bất biến và bắt buộc tuân thủ tuyệt đối** trong mọi phiên làm việc, dòng lệnh CLI và tương tác với dự án.

---

## 1. 🎯 Luồng Chấm Điểm & Đối Soát Trực Tiếp Với Kho Đáp Án Chuẩn (Direct Evaluation Pipeline)

- **Vai trò trung tâm:** Hệ thống tự động đối soát và chấm điểm bài làm của người học **trực tiếp từ kho đáp án và giải thích chính thức Cambridge 18 có sẵn trong `data/`** (`cambridge_18_answers_and_explanations.json` và `cambridge18_test_*.json`).
- **Quy tắc luồng làm việc mới:**
  - **KHÔNG bắt người dùng phải nhập tay đáp án qua chức năng "Luyện thi & Chấm bài"** (chức năng này đã được tinh gọn và loại bỏ khỏi giao diện).
  - Người học điền câu trả lời trực tiếp vào bảng làm bài tương tác (`.ielts-grid-answers`) trong Phiên Học Hôm Nay (Daily Session / Quartz) hoặc nộp bài viết Writing.
  - Khi người học bấm nộp bài ("🚀 Nộp Bài & Chấm Điểm Trực Tiếp"), hệ thống **tự động tra cứu đáp án chuẩn từ `data/`**, so khớp kết quả, tính điểm, ước lượng Band Score, trích xuất giải thích dẫn chứng và cập nhật trực tiếp vào Bảng Đối Soát trong file Markdown (SSOT) và cơ sở dữ liệu.
  - TUYỆT ĐỐI KHÔNG tự bịa hoặc đoán mò đáp án khi ngoài phạm vi dữ liệu đề chuẩn; chỉ đối soát theo dữ liệu chính thức đã được kiểm chứng.

---

## 2. ⚡ Cấu Trúc Hệ Thống, Bảo Mật Cổng Mạng & Cloudflare Tunnel (Network & Hardware Safety)

Để bảo vệ máy chủ cục bộ, tránh xung đột container (CVAT, Traefik, YOLO) và chuẩn bị xuất bản an toàn qua Cloudflare Zero Trust:

- **Bản Đồ Cổng Mạng Cố Định Khóa 127.0.0.1:**
  - Toàn bộ các cổng dịch vụ **BẮT BUỘC gán vào loopback `127.0.0.1`** (`127.0.0.1:port`) để chặn đứng mọi kết nối trực tiếp từ IP công cộng bên ngoài:
    - **PostgreSQL 16:** Ánh xạ host **`127.0.0.1:5433`** $ightarrow$ container `5432` (`DATABASE_URL=postgresql://noteai:noteai_secret_password@localhost:5433/noteai_pkm`). **TUYỆT ĐỐI KHÔNG DÙNG CỔNG 5432** (cổng này đã được container `cvat_db` sử dụng).
    - **Qdrant Vector DB:** Host **`127.0.0.1:6333`** (REST API) và **`127.0.0.1:6334`** (gRPC).
    - **FastAPI Backend Gateway:** Host **`127.0.0.1:8000`** (`http://127.0.0.1:8000`, docs tại `/docs`). Phục vụ API và kiêm luôn React SPA Frontend (`frontend/dist/`).
    - **Interactive React SPA Frontend (Dev Mode):** Host **`127.0.0.1:5173`** (`http://127.0.0.1:5173`).
- **Kiến Trúc Định Tuyến & Xác Thực:**
  - **Loại bỏ Nginx:** Hệ thống không dùng Nginx reverse proxy mà định tuyến công cộng trực tiếp qua **Cloudflare Tunnel (`cloudflared`)**.
  - **Màn Hình Đăng Nhập (Auth Guard):** Toàn bộ giao diện người dùng được bảo vệ bằng màn hình đăng nhập (mặc định: `admin` / `noteai2026`, cấu hình qua `backend/.env`).
- **An Toàn Phần Cứng & Tối Ưu Hóa CPU (Hardware Safety):**
  - Máy tính trang bị GPU NVIDIA T1200 Laptop (4GB VRAM). Để tránh tràn bộ nhớ VRAM và giữ GPU cho các tác vụ khác, **toàn bộ pipeline nhúng vector (RAG) BẮT BUỘC chạy tối ưu trên CPU** thông qua thư viện `fastembed` (Rust-backed ONNX Runtime với tập lệnh AVX2/AVX-512).
  - LLM suy luận sử dụng **Cloud API** (Google Gemini API / OpenAI API) để đạt tốc độ cao, không tốn RAM máy.

---

## 3. 🗂️ Cấu Trúc Thư Mục & Phân Cấp Tri Thức (Knowledge Graph Hierarchy)

- **Single Source of Truth (SSOT):** Toàn bộ ghi chú Markdown (`.md`) nằm trong thư mục `content/`. Website tĩnh, vector database Qdrant và cơ sở dữ liệu FSRS đều là các dẫn xuất tự động từ nguồn này.
- **Quy chuẩn phân cấp đồ thị (Hierarchy Rules):**
  - **Macro Nodes (`content/index.md`, `content/plans/index.md`):** Chỉ liên kết tới cấp tuần (`week-01`, `week-02`), không liên kết trực tiếp vào bài test con.
  - **Hub Nodes (`content/plans/week-XX/index.md`):** Đóng vai trò dashboard tổng quan của tuần, checklist tiến độ và thời khóa biểu micro-sessions (30–35 phút/phiên).
  - **Leaf Nodes (Bài test chi tiết, từ vựng):** File riêng lẻ cho từng kỹ năng (`test-1-listening.md`, `vocab-week-01.md`). **CHỈ ĐƯỢC liên kết ngược về Hub tuần cha**, không nối tắt về root index để bảo toàn tính phân cấp của Knowledge Graph.
- **Quy tắc đặt tên file (Kebab-case):**
  - `roadmap-<mục-tiêu>.md` (ví dụ: `roadmap-5.0-to-7.5.md`).
  - `vocab-<chủ-đề-hoặc-tuần>.md` (ví dụ: `vocab-week-01.md`).
  - `writing-task1-...md` / `writing-task2-...md`.
  - `speaking-part1-...md` / `speaking-part2-...md`.
  - `test-<số>-<kỹ-năng>.md` (ví dụ: `test-1-listening.md`).
- **Quy tắc Chu Kỳ Kế Hoạch Tuần (Weekly Calendar Boundary Rule):**
  - Kế hoạch trong tuần **BẮT BUỘC kết thúc vào ngày Chủ Nhật (CN)** của tuần đó, **TUYỆT ĐỐI KHÔNG kéo dài sang tuần khác** (không để Thứ 2, Thứ 3 tuần mới nằm trong tuần cũ).
  - Nếu khởi động giữa tuần (ví dụ Thứ 4, 14/10), tuần khởi đầu sẽ kéo dài từ Thứ 4 đến hết Chủ Nhật cùng tuần (`14/10 – 18/10`).
  - Tuần kế tiếp sẽ bắt đầu trọn vẹn từ Thứ 2 đến Chủ Nhật tiếp theo (`19/10 – 25/10`).

---

## 4. 🏷️ Quy Chuẩn Schema YAML Frontmatter Nghiêm Ngặt

Mọi file Markdown trong `content/` **bắt buộc** phải có YAML Frontmatter hợp lệ:

- **`title:`** Bắt buộc, chuỗi Tiếng Việt rõ nghĩa.
  - **Quy tắc Tiêu Đề Ngắn Gọn Theo Ngày Tháng (Concise Plan Execution Date Rule):** Khi tạo các file Markdown thuộc kế hoạch học tập (`plans/week-XX/...`, các bài test `test-*.md`, từ vựng `vocab-*.md`, hoặc các phiên luyện tập hàng ngày), **BẮT BUỘC chỉ đưa ngày và tháng (`DD/MM`) thực hiện theo plan vào đầu trường `title`, và viết tên thật ngắn gọn, súc tích** (bỏ bớt các tiền tố dài như "Bài Làm", "Sổ Từ Vựng Trọng Tâm", bỏ năm `/YYYY`) để tiêu đề hiển thị trọn vẹn, dễ đọc trên Explorer/Sidebar/Tab mà không bị tràn hay cắt cụt chữ.
    - **Bài test / Nhiệm vụ trong ngày:** Định dạng `[DD/MM] Tên Ngắn Gọn`
      - *Ví dụ:* `title: "[14/10] Test 1 Listening"` (thay vì `[14/10/2026] Bài Làm Test 1 Listening (Cam 18)`)
      - *Ví dụ:* `title: "[15/10] Test 1 Reading P3"` (thay vì `[15/10/2026] Bài Làm Test 1 Reading Passage 3 (Cam 18)`)
      - *Ví dụ:* `title: "[16/10] Test 1 Writing"` (thay vì `[16/10/2026] Bài Làm Test 1 Writing (Cam 18)`)
    - **Hub kế hoạch tuần / Sổ từ vựng tuần:** Định dạng `[DD/MM - DD/MM] Tên Ngắn Gọn` (kết thúc vào Chủ Nhật).
      - *Ví dụ:* `title: "[14/10 - 18/10] Kế Hoạch Tuần 1"`
      - *Ví dụ:* `title: "[14/10 - 18/10] Từ Vựng Tuần 1"` (thay vì `[14/10 – 20/10/2026] Sổ Từ Vựng Trọng Tâm Tuần 1`)
- **`aliases:`** Khuyến nghị cho bài học/ngữ pháp và bắt buộc cho từ vựng để hỗ trợ tìm kiếm chéo và semantic linking (ví dụ: `[vocab-week-01, cam18-vocab]`).
- **`tags:`** Danh sách ít nhất 1 tag phân loại: kỹ năng (`listening`, `reading`), nguồn đề (`cambridge18`), tuần học (`week-01`), và cấp độ CEFR (`b2-c1`).
- **`sr-due:`** Định dạng `YYYY-MM-DD` đối với tài liệu từ vựng/ôn tập để tích hợp thuật toán Spaced Repetition.

---

## 5. ✍️ Cú Pháp Nhập Liệu Bài Làm Siêu Tốc (Shorthand Syntax)

Hệ thống hỗ trợ và tự động chuẩn hóa các cú pháp tốc ký của người học:

- **Làm đúng:** `3 dentist`, `12 a`, `24 c`.
- **Làm sai (đối chiếu):** `1 dw137yz - dw307yz`, `4 car - parking / lý do: nghe nhầm danh từ`.
- **Bỏ trống lúc làm bài:** `16 - b / lý do: audio nói nhanh không kịp bắt keyword`.

---

## 6. 🧠 Quy Chuẩn Động Cơ Trí Nhớ FSRS v4 (Spaced Repetition)

- **Thuật toán:** Sử dụng công thức toán học **DSR (Difficulty, Stability, Retrievability)** của FSRS v4 qua thư viện Python `fsrs`.
- **Lưu trữ CSDL:** Dữ liệu thẻ lưu vào PostgreSQL (`flashcards` và `review_logs`).
- **4 mức đánh giá chuẩn:**
  1. `Again (1)`: Quên hoàn toàn, reset chu kỳ học.
  2. `Hard (2)`: Nhớ được nhưng rất khó khăn, tăng độ khó $D$.
  3. `Good (3)`: Nhớ đúng với nỗ lực vừa phải (mặc định tối ưu).
  4. `Easy (4)`: Nhớ lập tức và rất dễ dàng, tăng mạnh độ ổn định $S$.
- **Đồng bộ song song:** Hệ thống hỗ trợ sinh file `content/assets/IELTS_Master_Deck.apkg` với Deck ID cố định `2026100901` (`IELTS - NoteAI Master Deck`) để tương thích ngược với Anki trên điện thoại.

---

## 7. 🤖 Nguyên Tắc Vận Hành Đa Đặc Vụ (Autonomous Multi-Agent Workflow)

- **Evaluator Agent:**
  - Chuyên trách chấm bài, phân tích lỗi sai, đối chiếu tiêu chí IELTS (GRA, CC, TR/TA, LR).
  - Bắt buộc kiểm tra Guardrail trước khi xuất kết quả: không suy diễn câu trả lời khi thiếu đáp án chuẩn.
  - Truy vấn vector DB (Qdrant) để lấy ngữ cảnh từ vựng và quy tắc ngữ pháp đã học.
- **Planning Agent:**
  - Phân tích telemetry và lịch sử lỗi sai từ PostgreSQL để đề xuất lịch học thích ứng (Micro-sessions 30–35 phút) cho các tuần tiếp theo.
- **Watchdog Daemon:**
  - Lắng nghe sự kiện ghi file trong `content/` và kích hoạt ngầm (Asynchronous Background Task) việc re-index vector vào Qdrant và đồng bộ FSRS cards mà không khóa tiến trình người dùng.

---

## 8. 📄 Trình Xem PDF & Giao Diện Quartz (Layout UX Rules)

- **PDF Viewer:** Mọi file PDF nhúng trong tài nguyên đều phải có thanh công cụ hỗ trợ 2 nút: `↗️ Mở trong tab mới` và `⬇️ Tải xuống PDF`.
- **Right Sidebar:** Cột bên phải chỉ giữ lại `TableOfContents` để tiện tra cứu nội dung. Tuyệt đối không bật lại quả cầu Graph View ở cột bên phải nhằm tránh phân tâm.

---

## 9. 🛡️ Pipeline Kiểm Chứng Hình Thức (Formal Verification Pipeline)

Trước khi thực hiện Git commit & push, bắt buộc chạy pipeline kiểm chứng qua lệnh:

```bash
python scripts/_py_/run_pipeline.py
# (hoặc: python scripts/run_pipeline.py)
```

Pipeline kiểm chứng thực thi 4 chặng nghiêm ngặt:

1. **Kiểm tra Schema Frontmatter & Dead Link Checker:** Xác minh 100% file đủ frontmatter và không có bất kỳ liên kết hỏng (dead link) nào.
2. **Markdown Linter (`markdownlint-cli`):** Đảm bảo cú pháp Markdown chuẩn mực theo `.markdownlint.json`.
3. **Đồng bộ Dữ Liệu FSRS & Anki:** Kiểm tra và đồng bộ thẻ từ vựng mới vào PostgreSQL / `.apkg`.
4. **Kiểm thử biên dịch React SPA Production (`cd frontend && npm run build`):** Xác nhận giao diện người dùng build thành công 100%.

**Sau khi vượt qua hoàn toàn:**

- Commit với thông điệp chuẩn Conventional Commits: `docs: add note <tên>`, `feat: ...`, `fix: ...`.
- Đẩy mã nguồn lên kho lưu trữ từ xa: `git push origin main`.

---

## 10. 📐 Quy Chuẩn Template Bắt Buộc Toàn Dự Án (Mandatory Project Templates)

- **Nguyên tắc cốt lõi:** Cả **Trợ lý AI (Antigravity)** và **AI Cronjob / Autonomous Planning Agent** BẮT BUỘC tuân thủ 100% hệ thống mẫu chuẩn tại thư mục `templates/` khi khởi tạo hoặc cập nhật bất kỳ ghi chú Markdown nào trong `content/`.
- **7 Mẫu Template Chuẩn:**
  1. `templates/template-weekly-plan.md` $\rightarrow$ Hub tuần (`content/plans/week-XX/index.md`)
  2. `templates/template-listening-session.md` $\rightarrow$ Phiên Listening (`test-X-listening-p*.md`)
  3. `templates/template-reading-session.md` $\rightarrow$ Phiên Reading (`test-X-reading-p*.md`)
  4. `templates/template-writing-session.md` $\rightarrow$ Phiên Writing (`test-X-writing.md`)
  5. `templates/template-speaking-session.md` $\rightarrow$ Phiên Speaking (`test-X-speaking.md`)
  6. `templates/template-vocab-week.md` $\rightarrow$ Sổ từ vựng tuần (`vocab-week-XX.md`)
  7. `templates/template-review-week.md` $\rightarrow$ Phiên Review tổng kết tuần (`review-week-XX.md`)
- **Ràng buộc tương tác bất biến (Inviolable Interactive Constraints):**
  - Mọi bài làm Listening và Reading **BẮT BUỘC chứa thẻ container `.ielts-sheet-card` cùng `<div class="ielts-grid-answers"></div>`** để engine JavaScript tự động render bảng điền đáp án, bộ đếm giờ và thanh trạng thái lưu LocalStorage.
  - Sổ từ vựng tuần **BẮT BUỘC có trường `sr-due: "YYYY-MM-DD"`** và bảng từ vựng Markdown đúng chuẩn (`| Từ Vựng (Front) | Từ Loại | Phiên Âm (IPA) | Ý Nghĩa Tiếng Việt (Back) | ...`) để FSRS v4 tự động đồng bộ vào PostgreSQL và `IELTS_Master_Deck.apkg`.
  - Mọi bài con (Leaf Node) **BẮT BUỘC chỉ liên kết ngược về Hub tuần cha `[[plans/week-XX/|...]]`**, không nối tắt về root index.

