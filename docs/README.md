# 📚 Thư Mục Tài Liệu & Đặc Tả Hệ Thống (NoteAI.v2 Docs)

Thư mục này tập hợp toàn bộ các tài liệu đặc tả kiến trúc, tiêu chuẩn kỹ thuật, thiết kế hệ thống và quy trình vận hành của **NoteAI.v2** (Local Autonomous PKM).

---

## 📑 Danh Mục Tài Liệu

| Tài Liệu                                                                      | Mục Đích & Nội Dung Chi Tiết                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| :---------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**`ARCHITECTURE.md`**](file:///d:/Ielts/code/NoteAI.v2/docs/ARCHITECTURE.md) | **Đặc Tả Kiến Trúc Hệ Thống (System Architecture):**<br>• Sơ đồ Topology toàn hệ thống (Storage, Docker Infra, FastAPI Backend, React SPA, Quartz SSG).<br>• Luồng xử lý sự kiện Event-Driven Watchdog $\rightarrow$ LangGraph State Machine.<br>• Mô hình toán học DSR của FSRS v4 & Sơ đồ CSDL quan hệ 3NF.<br>• Pipeline truy xuất ngữ nghĩa Vector RAG tối ưu hóa CPU (FastEmbed + Qdrant).                                                                                                                                                                                   |
| [**`STANDARDS.md`**](file:///d:/Ielts/code/NoteAI.v2/docs/STANDARDS.md)       | **Quy Chuẩn Kỹ Thuật & Mã Nguồn (Engineering Standards):**<br>• Quy chuẩn Backend: Python 3.12, Pydantic v2, SQLModel, Controller-Service-Repository, Async/Await.<br>• Quy chuẩn Frontend: React 19, TypeScript strict mode, bảng màu Apple Minimalist (`#f5f5f7` / `#1c1c1e` / `#0071e3`), TanStack Query keys.<br>• Quy chuẩn Markdown & Knowledge Base: YAML Frontmatter schema, Kebab-case naming, Shorthand test attempt syntax.<br>• Quy chuẩn Git: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) và quy tắc Fail-Fast trước khi commit. |

---

## 🤖 Quy Tắc AI & Vận Hành Trợ Lý

- [**`AGENTS.md`**](file:///d:/Ielts/code/NoteAI.v2/AGENTS.md) & [**`GEMINI.md`**](file:///d:/Ielts/code/NoteAI.v2/GEMINI.md): Bộ quy tắc bất biến cho AI (Nguyên tắc vàng không tự đoán đáp án/Band score, quy chuẩn cổng mạng, an toàn phần cứng CPU-Embeddings) được đặt tại thư mục gốc để tương thích với cơ chế tự động nạp của AI agent.
