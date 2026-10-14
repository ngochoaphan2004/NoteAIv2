# 🌿 NoteAI.v2: Local Autonomous PKM & IELTS Digital Garden

> **Hệ Thống Quản Trị Tri Thức Cá Nhân Tự Trị (Local Autonomous Personal Knowledge Management) & Vườn Tri Thức Số Luyện Thi IELTS**, vận hành theo kiến trúc **Hybrid Dual-Engine**: kết hợp giữa Web Tĩnh siêu tốc (Quartz v4) và Nền tảng AI Kỹ thuật cao (FastAPI, LangGraph, Qdrant, FSRS v4, React SPA).

---

## 🚀 Các Điểm Sáng Kỹ Thuật (Feature Highlights)

- **🧠 Động Cơ Trí Nhớ FSRS v4 (Spaced Repetition):** Thoát ly Anki để trực tiếp quản lý thuật toán lặp lại ngắt quãng theo mô hình toán học **DSR (Difficulty, Stability, Retrievability)**, lưu trữ trong PostgreSQL quan hệ (3NF).
- **🤖 Hệ Thống Đa Đặc Vụ (Autonomous Multi-Agent Workflow):** Điều phối qua **LangGraph** và **Pydantic v2**. Trang bị `Evaluator Agent` (chấm bài thi IELTS theo tiêu chí GRA, CC, LR, TR) và `Planning Agent` (phân bổ lịch học thích ứng Micro-sessions 30–35 phút).
- **🔍 Vector RAG Pipeline Tối Ưu Hóa CPU:** Lập chỉ mục ngữ nghĩa toàn bộ ghi chú Markdown vào **Qdrant Vector DB** thông qua **`fastembed`** (Rust ONNX Runtime AVX2/AVX-512), bảo toàn 4GB VRAM của GPU máy chủ.
- **⚡ FastAPI Backend Gateway:** Cung cấp REST API hiệu năng cao chuẩn OpenAPI/Swagger theo mô hình `Controller - Service - Repository`, tích hợp `Watchdog` daemon tự động bắt sự kiện lưu file Markdown.
- **💻 Giao Diện Tương Tác SPA (Vite + React 19):** Trải nghiệm lật flashcard mượt mà với phím tắt, biểu đồ tỷ lệ ghi nhớ (Retention Curve), và bảng phân tích điểm số trực quan.
- **🛡️ Pipeline Kiểm Chứng Hình Thức (Formal Verification):** Tự động phát hiện 100% liên kết hỏng (Dead Links) và kiểm tra chuẩn YAML Frontmatter trước khi cho phép Git commit.

---

## 🏛️ Bản Đồ Cổng Mạng (Port Allocations)

Hệ thống được thiết kế để không xung đột với các container khác trên máy chủ:

| Phân Hệ              |  Cổng Truy Cập   | Mục Đích                                                    |
| :------------------- | :--------------: | :---------------------------------------------------------- |
| **PostgreSQL 16**    | `localhost:5433` | CSDL Thẻ nhớ FSRS & Lịch sử ôn tập (Container port: `5432`) |
| **Qdrant Vector DB** | `localhost:6333` | REST API tìm kiếm ngữ nghĩa Vector Memory                   |
| **FastAPI Backend**  | `localhost:8000` | REST API Gateway & Swagger Docs (`/docs`)                   |
| **Interactive SPA**  | `localhost:5173` | Giao diện tương tác Flashcards & Analytics                  |
| **Quartz v4 Garden** | `localhost:8088` | Trang đọc Digital Garden tĩnh (và deploy GitHub Pages)      |

---

## 🛠️ Hướng Dẫn Khởi Chạy Nhanh (Quick Start)

### 1. Yêu Cầu Môi Trường

- **Python:** `>= 3.12`
- **Node.js:** `>= 22`
- **Docker & Docker Compose**

### 2. Bước 1: Khởi Động Hạ Tầng Container (Postgres & Qdrant)

```powershell
docker-compose -f docker/docker-compose.yml up -d
```

Xác nhận 2 container `noteai_postgres` (port `5433`) và `noteai_qdrant` (port `6333`) đã ở trạng thái `healthy`.

### 3. Bước 2: Cấu Hình Môi Trường Backend

Tạo file `backend/.env` từ file mẫu:

```powershell
cp backend/.env.example backend/.env
```

Điền khóa `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) của bạn vào `backend/.env`.

### 4. Bước 3: Cài Đặt Dependencies & Khởi Chạy Backend

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Truy cập tài liệu API tương tác tại: `http://localhost:8000/docs`.

### 5. Bước 4: Khởi Chạy Giao Diện Tương Tác Frontend

Mở một cửa sổ dòng lệnh khác:

```powershell
cd frontend
npm install
npm run dev
```

Truy cập giao diện tại: `http://localhost:5173`.

### 6. Bước 5: Xem Trước Khu Vườn Tri Thức Tĩnh (Quartz v4)

```powershell
npx quartz build --serve --port 8088
```

---

## 📚 Tài Liệu Hướng Dẫn Liên Quan

- 🤖 [**`AGENTS.md`**](file:///d:/Ielts/code/NoteAI.v2/AGENTS.md): Bộ quy tắc bất biến cho AI (Nguyên tắc vàng không đoán đáp án, quy chuẩn phân cấp tri thức).
- 🏛️ [**`docs/ARCHITECTURE.md`**](file:///d:/Ielts/code/NoteAI.v2/docs/ARCHITECTURE.md): Bản đặc tả kiến trúc kỹ thuật chi tiết với các sơ đồ Mermaid.
- 📐 [**`docs/STANDARDS.md`**](file:///d:/Ielts/code/NoteAI.v2/docs/STANDARDS.md): Bộ quy chuẩn lập trình Python, React, Markdown Schemas và Conventional Commits.
