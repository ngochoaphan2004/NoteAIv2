# 🛠️ NoteAI.v2 - Scripts Directory Reference

Thư mục chứa các công cụ tự động hóa điều phối hệ thống, kiểm chứng hình thức (Pipeline), đồng bộ VPS và quản trị dữ liệu.

---

## 🚀 1. Các Script Batch (`.bat`) Quản Trị VPS

| File Script | Công Dụng Chính | File & Thư Mục Tương Tác |
| :--- | :--- | :--- |
| **`vps_update.bat`** | **1-Click Build & Deploy lên VPS:**<br>• Biên dịch Frontend SPA & Quartz<br>• Đóng gói mã nguồn, kế hoạch (`plans/`) và ghi chú (`.md`)<br>• Tự động sao lưu server trước khi giải nén đè<br>• *Mặc định Fast Mode:* Bỏ qua 112MB Data/Assets để đẩy siêu tốc trong 5s. | • `frontend/` (`npm run build`)<br>• `quartz/` (`npx quartz build`)<br>• `backend/app/services/plan_service.py`<br>• `scripts/update_vps.sh`<br>• VPS: `/opt/noteai/` |
| **`vps_pull_content.bat`** | **1-Click Kéo bài làm từ VPS về Local:**<br>• Kéo toàn bộ bài thi (Writing, Listening, Reading) & điểm số từ VPS về máy tính<br>• Tự động sao lưu an toàn 2 đầu (Local `backups/` & VPS `backups/`) trước khi cập nhật. | • `scripts/_py_/pull_server_content.py`<br>• VPS: `/opt/noteai/content/` (`*.md`)<br>• Cập nhật vào: `content/`<br>• Lưu backup: `backups/content_local_*/` |
| **`vps_update_assets.bat`** | **Đồng bộ Data & Assets nặng lên VPS:**<br>• Đẩy riêng Audio MP3 (110MB), Sách PDF, Flashcard `.apkg` và Database đáp án JSON Cam 18 khi có tài liệu mới<br>• Tự động tái tạo symlink audio trên web Quartz. | • `content/assets/` (Audio, PDF, APKG)<br>• `content/data/` (JSON Keys Cam 18)<br>• VPS: `/opt/noteai/content/assets/`<br>• VPS: `/opt/noteai/public/assets/audio/` |
| **`clean_content.bat`** | **Dọn sạch server từ xa qua SSH:**<br>• Hỗ trợ 2 chế độ: *(1) Xóa content & build cũ*, hoặc *(2) Full Reset toàn bộ code để deploy mới 100%*<br>• Bảo toàn 100% runtime: `venv/`, `node_modules/`, `package*.json`, `backend/.env`, Audio. | • Gọi SSH: `/opt/noteai/clean_content.sh`<br>• VPS: Dọn dẹp `/opt/noteai/` |

---

## 🐧 2. Các Script Chạy Trực Tiếp Trên VPS Linux

*   **`clean_content.sh`** *(và `clean_content.bat` trên VPS)*: Script bash dọn dẹp môi trường trên VPS, bảo lưu `.env` và thư viện nặng trước khi xóa.
*   **`update_vps.sh`**: Script tự động chạy sau khi giải nén cập nhật trên VPS: kiểm tra `requirements.txt`, chạy init DB PostgreSQL, restart service `noteai-backend` và reload `nginx`.
*   **`noteai_nginx.conf`**: Bản mẫu cấu hình Nginx reverse proxy cho React SPA (Port 80) và Quartz Digital Garden (Port 8088).

---

## 🐍 3. Các Script Python Trong `scripts/_py_/`

| File Python | Công Dụng |
| :--- | :--- |
| **`run_pipeline.py`** | **Formal Verification Pipeline (4 chặng):** Điều phối kiểm chứng Schema Frontmatter, Dead Links, Markdownlint, Anki Sync và Quartz Build trước khi Git Commit/Push. |
| **`verify_knowledge_base.py`** | Quét toàn bộ `content/`, xác minh 100% schema YAML frontmatter và kiểm tra tính toàn vẹn liên kết (Dead Link Checker). |
| **`anki_sync.py`** | Trích xuất từ vựng từ các ghi chú Markdown và đóng gói file Anki Master Deck tại `content/assets/IELTS_Master_Deck.apkg`. |
| **`pull_server_content.py`** | Core engine kết nối SSH/SCP, đóng gói và tải các file `.md` bài thi từ VPS về máy tính có cơ chế backup kép. |
| **`import_audio.py`** | Quét file MP3 Cambridge 18 gốc, đổi tên chuẩn hóa và tạo `audio_metadata.json` cho Web Audio Player. |
| **`extract_test.py`** | Pipeline AI sử dụng Gemini API OCR trích xuất đáp án và lời giải chi tiết từ sách Cambridge 18 PDF. |
| **`merge_cambridge18.py`** | Hợp nhất 4 file JSON Test 1–4 thành master database `cambridge_18_answers_and_explanations.json`. |
