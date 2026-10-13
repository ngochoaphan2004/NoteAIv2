# 📐 BỘ QUY CHUẨN KỸ THUẬT & MÃ NGUỒN: NOTEAI.V2

Tài liệu này quy định toàn bộ các tiêu chuẩn kỹ thuật (Engineering Standards), quy ước viết mã (Code Conventions), định dạng dữ liệu (Data Schemas) và quy trình Git đối với dự án **NoteAI.v2**.

---

## I. QUY CHUẨN LẬP TRÌNH PYTHON & BACKEND (FASTAPI / PYDANTIC)

### 1. Phiên Bản & Môi Trường

* **Runtime:** Python `>=3.12`.
* **Quản lý phụ thuộc:** Liệt kê rõ ràng phiên bản trong `backend/requirements.txt` (hoặc `pyproject.toml`).
* **Format & Linter:** Tuân thủ chuẩn PEP 8. Khuyến khích sử dụng `ruff` hoặc `black` để định dạng mã nguồn.

### 2. Ép Kiểu Tĩnh Nghiêm Ngặt (Strict Type Hinting)

* 100% các hàm, phương thức (Methods) và biến API đều phải có Type Annotations đầy đủ.
* Tuyệt đối không sử dụng kiểu dữ liệu `Any` khi có thể định nghĩa cụ thể:

  ```python
  # ❌ SAI
  def process_card(data):
      return data.get("id")

  # ✅ ĐÚNG
  from typing import Optional
  import uuid

  def process_card(card_id: uuid.UUID, rating: int) -> Optional[dict[str, str]]:
      ...
  ```

### 3. Pydantic v2 & Data Validation

* Mọi dữ liệu Request Body, Response Model và State của Agent đều phải định nghĩa bằng `pydantic.BaseModel` (v2).
* Sử dụng `Field(description=...)` cho các trường dữ liệu để tự động sinh Swagger OpenAPI docs rõ ràng.
* Áp dụng `model_validate` và `@field_validator` để chuẩn hóa input.

### 4. Kiến Trúc Controller - Service - Repository

* **Controller (`app/api/v1/`):** Chỉ làm nhiệm vụ nhận request, gọi service, bắt lỗi HTTP (`HTTPException`) và trả về schema chuẩn. Tuyệt đối không viết logic nghiệp vụ phức tạp trong controller.
* **Service (`app/services/`):** Chứa thuần túy logic nghiệp vụ (FSRS calculation, RAG search, Prompt compilation). Độc lập với HTTP request context để có thể viết Unit Test dễ dàng.
* **Repository / Database (`app/core/database.py`, `app/models/`):** Quản lý kết nối SQLModel, session context manager và thao tác CRUD cơ bản.

### 5. Xử Lý Bất Đồng Bộ (Async / Await)

* Mọi I/O bound tasks (truy vấn DB qua async engine, gọi Cloud LLM API qua HTTP, truy vấn Qdrant REST) phải dùng hàm `async def` và `await`.
* Các tác vụ tính toán nặng trên CPU (như mã hóa vector ONNX) hoặc tác vụ nền (re-indexing Markdown) phải được đẩy vào `FastAPI.BackgroundTasks` hoặc thread pool (`asyncio.to_thread`) để không làm nghẽn Event Loop.

---

## II. QUY CHUẨN FRONTEND REACT & TYPESCRIPT

### 1. Nền Tảng & Công Nghệ

* **Framework:** React 19 chạy trên Vite 6.
* **Ngôn ngữ:** TypeScript ở chế độ nghiêm ngặt (`"strict": true` trong `tsconfig.json`).
* **Styling:** Tailwind CSS (áp dụng Bảng màu Apple Minimalist).

### 2. Bảng Màu Chuẩn (Apple Minimalist Palette)

* **Light Mode:**
  * Background: `#f5f5f7` (macOS Window background)
  * Card Surface: `#ffffff`
  * Text Primary: `#1d1d1f`
  * Text Secondary: `#86868b`
  * Border / Divider: `#d2d2d7`
  * Accent Primary: `#0071e3` (Apple Blue)
* **Dark Mode:**
  * Background: `#1c1c1e` (Apple System Dark)
  * Card Surface: `#2c2c2e`
  * Text Primary: `#f5f5f7`
  * Text Secondary: `#a1a1a6`
  * Border / Divider: `#38383a`
  * Accent Primary: `#2997ff`

### 3. Cấu Trúc Thư Mục Frontend

```text
frontend/src/
├── components/          # UI Components tái sử dụng (Button, Card, Modal...)
├── hooks/               # Custom hooks & TanStack Query wrappers
├── pages/               # Các trang giao diện (ReviewPage, DashboardPage...)
├── services/            # Client kết nối REST API (Fetch / Axios wrappers)
├── types/               # TypeScript interfaces & types đồng bộ với Pydantic
└── App.tsx
```

### 4. Quản Lý Trạng Thái & Data Fetching (TanStack Query)

* Không dùng `useEffect` thủ công để fetch dữ liệu từ API. Toàn bộ logic tương tác REST API phải thông qua `useQuery` và `useMutation`.
* Quy chuẩn Query Keys rõ ràng theo cụm tài nguyên:

  ```typescript
  // ✅ ĐÚNG
  const { data: dueCards } = useQuery({
    queryKey: ['flashcards', 'due'],
    queryFn: fetchDueFlashcards,
  });
  ```

---

## III. QUY CHUẨN DỮ LIỆU MARKDOWN & KNOWLEDGE GRAPH

### 1. Quy Tắc Đặt Tên Tệp (File Naming)

* 100% tên tệp và thư mục viết bằng chữ thường, phân cách bằng dấu gạch ngang (kebab-case).
* Tiền tố định danh rõ ràng:
  * `plans/week-XX/index.md` (Hub tuần).
  * `plans/week-XX/test-<số>-<kỹ-năng>.md` (Leaf node bài thi).
  * `plans/week-XX/vocab-week-XX.md` (Sổ từ vựng tuần).
  * `roadmap-<mục-tiêu>.md` (Chiến lược dài hạn).
  * `grammar-<chủ-đề>.md` (Chuyên đề ngữ pháp).

### 2. Schema YAML Frontmatter Bắt Buộc

Mọi file trong `content/` bắt buộc phải có Frontmatter ở đầu tệp:

```yaml
---
title: "Tiêu đề tiếng Việt rõ ràng, thân thiện"
aliases:
  - slug-tieng-anh
  - tu-dong-nghia
tags:
  - ielts
  - listening
  - cambridge18
  - week-01
sr-due: "2026-10-15"  # Bắt buộc đối với tài liệu từ vựng/ôn tập
---
```

### 3. Quy Chuẩn Shorthand Syntax Bài Làm

Để người học nhập liệu nhanh nhất mà không cần format bảng phức tạp:

* **Câu làm đúng:** `<số_câu> <đáp_án>` (Ví dụ: `3 dentist`, `12 a`).
* **Câu làm sai:** `<số_câu> <bạn_chọn> - <đáp_án_đúng> / <lý_do_sai>`
  *(Ví dụ: `1 dw137yz - dw307yz / lý do: nghe nhầm chữ cái w thành 3`)*.
* **Câu bỏ trống:** `<số_câu> - <đáp_án_đúng> / <lý_do>`
  *(Ví dụ: `16 - b / lý do: bỏ lỡ do mải chú ý câu trước`)*.

### 4. Bảng Phân Tích Lỗi Sai Chuẩn 5 Cột (Error Drill Table)

Khi xuất bảng chữa đề, bắt buộc dùng cấu trúc:

```markdown
| Câu | Loại Bẫy / Nguyên Nhân | Đáp Án Của Bạn | Đáp Án Đúng | Phân Tích & Giải Pháp |
| :---: | :--- | :---: | :---: | :--- |
| **1** | Phát âm số/chữ cái | `dw137yz` | `dw307yz` | Nhầm âm /w/ và /3/, cần luyện drill nghe mã bưu chính |
```

---

## IV. QUY TRÌNH KIỂM SOÁT PHIÊN BẢN & GIT (VERSION CONTROL)

### 1. Conventional Commits Format

Mọi commit phải tuân theo cấu trúc:

```text
<type>(<scope>): <mô tả ngắn bằng tiếng Anh hoặc tiếng Việt>
```

* **`feat:`** Thêm tính năng mới (ví dụ: `feat(fsrs): add retention rate calculation endpoint`).
* **`fix:`** Sửa lỗi (ví dụ: `fix(rag): resolve table splitting bug in markdown parser`).
* **`docs:`** Thêm/sửa tài liệu hoặc ghi chú bài học (ví dụ: `docs(week-02): add test 2 listening attempt`).
* **`refactor:`** Tái cấu trúc mã nguồn không làm thay đổi tính năng.
* **`test:`** Bổ sung unit tests hoặc integration tests.
* **`chore:`** Thay đổi cấu hình, dependencies, tooling.

### 2. Quy Tắc "Fail-Fast" Trước Khi Commit

* Tuyệt đối không bỏ qua các lỗi linter hoặc dead links.
* Bắt buộc chạy `python scripts/run_pipeline.py` trước khi commit. Nếu pipeline báo lỗi (Exit code $\neq 0$), lập tức sửa dứt điểm lỗi trước khi thử commit lại.
