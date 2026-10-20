# 📐 NoteAI.v2 - Centralized Project Templates Specification

> **BỘ QUY TẮC MẪU CHUẨN TOÀN DỰ ÁN (MANDATORY PROJECT TEMPLATES)**  
> Cả **Trợ lý AI (Antigravity)** và **AI Cronjob / Autonomous Planning Agent** BẮT BUỘC tuân thủ 100% các mẫu chuẩn này khi khởi tạo hoặc cập nhật bất kỳ ghi chú Markdown nào trong `content/`.

---

## 📌 1. Danh Mục Các Template Chuẩn

Mọi file Markdown trong dự án phải thuộc một trong các mẫu chuẩn sau:

| Tên Template | File Mẫu Chuẩn | Đường Dẫn Thực Tế | Quy Chuẩn Tiêu Đề (`title:`) |
| :--- | :--- | :--- | :--- |
| **Hub Kế Hoạch Tuần** | `templates/template-weekly-plan.md` | `content/plans/week-XX/index.md` | `"[DD/MM - DD/MM] Kế Hoạch Tuần X"` |
| **Listening Micro-session** | `templates/template-listening-session.md` | `content/plans/week-XX/test-X-listening-p*.md` | `"[DD/MM] Test X Listening P*"` |
| **Reading Micro-session** | `templates/template-reading-session.md` | `content/plans/week-XX/test-X-reading-p*.md` | `"[DD/MM] Test X Reading P*"` |
| **Writing Task Session** | `templates/template-writing-session.md` | `content/plans/week-XX/test-X-writing.md` | `"[DD/MM] Test X Writing Task *"` |
| **Speaking Task Session** | `templates/template-speaking-session.md` | `content/plans/week-XX/test-X-speaking.md` | `"[DD/MM] Test X Speaking Part *"` |
| **Sổ Từ Vựng Tuần** | `templates/template-vocab-week.md` | `content/plans/week-XX/vocab-week-XX.md` | `"[DD/MM - DD/MM] Từ Vựng Tuần X"` |
| **Bài Ôn Tập Tổng Kết** | `templates/template-review-week.md` | `content/plans/week-XX/review-week-XX.md` | `"[DD/MM] Review Tuần X"` |

---

## 🛡️ 2. Các Quy Tắc Bất Biến (Inviolable Template Rules)

1. **Quy tắc Tiêu đề Ngắn Gọn Theo Ngày Tháng:**
   - Ngày thực hiện `[DD/MM]` đặt ở đầu trường `title:`.
   - Bỏ năm `/YYYY`, bỏ tiền tố rườm rà ("Bài làm...", "Sổ từ vựng trọng tâm...").
   - Kế hoạch tuần và sổ từ vựng: `[DD/MM - DD/MM] Tên Ngắn Gọn` (kết thúc vào **Chủ Nhật**).
2. **Quy tắc Bảng Điền Đáp Án Tương Tác (Listening & Reading):**
   - Phải có thẻ bao ngoài `<div class="ielts-sheet-card" data-sheet-id="..." data-start-q="..." data-end-q="..." data-timer="...">`.
   - Phải có `.ielts-card-header` chứa `.ielts-timer-widget` (nút ▶️, ⏸️, 🔄).
   - Phải có `.ielts-stats-bar` chứa `.ielts-sheet-progress` và `.ielts-sheet-save-text`.
   - **BẮT BUỘC có `<div class="ielts-grid-answers"></div>`** để engine JavaScript tự động sinh các ô input nhập liệu.
   - Phải có cụm nút tác vụ `.ielts-card-actions`: `🚀 Gửi Câu Trả Lời Cho AI`, `📋 Sao Chép Shorthand`, `🗑️ Xóa Bài Làm`.
3. **Quy tắc Mạng Lưới Kiến Thức (Bidirectional Linking):**
   - Mọi bài con (Leaf Node) **chỉ được liên kết ngược về Hub cha của nó (`[[plans/week-XX/|Kế Hoạch Tuần X]]`)**, không nối tắt về root index.
   - Hub tuần cha liên kết tới tất cả các bài con trong tuần.
4. **Quy tắc Chu Kỳ Tuần (Sunday Boundary):**
   - Lịch tuần luôn kết thúc vào Chủ Nhật, không bao giờ kéo dài sang Thứ 2 của tuần sau.
