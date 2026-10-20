---
title: "[{{DATE_DD_MM}}] Test {{TEST_NUM}} Reading {{PASSAGE_LABEL_SHORT}}"
aliases:
  - test-{{SOURCE_SLUG}}-test{{TEST_NUM}}-reading-{{PASSAGE_SLUG}}
  - test-{{TEST_NUM}}-reading-{{PASSAGE_SLUG}}
tags:
  - reading
  - test-attempt
  - {{SOURCE_TAG}}
  - {{PASSAGE_TAG_1}}
  - {{PASSAGE_TAG_2}}
  - week-{{WEEK_PADDED}}
---

# 📖 Bài Làm: {{SOURCE_NAME}} - Test {{TEST_NUM}} Reading ({{PASSAGE_LABEL_FULL}})

> **Tuần thực hiện:** [[plans/week-{{WEEK_PADDED}}/|Kế Hoạch Tuần {{WEEK_NUM}} ({{START_DD_MM}} – {{END_DD_MM}})]] — Phiên {{DAY_NAME}}: Reading {{PASSAGE_LABEL_FULL}}  
> **Chủ đề bài đọc:**  
{{PASSAGE_TOPICS}}
> **Thời lượng:** 35 phút ({{TEST_TIMER}} phút làm {{TOTAL_QUESTIONS}} câu + {{REVIEW_TIMER}} phút lập bảng Keyword Mapping và trích xuất từ vựng)  
> **Mục đích:** Rèn kỹ năng quét từ khóa (Scanning), định vị thông tin nhanh (Skimming) và xử lý các bẫy True/False/Not Given, Matching Information.

---

## 📑 Đề Thi ({{PAGE_RANGE_STR}})

<details open class="ielts-exam-prompt">
<summary><b>📄 Đề Bài: {{SOURCE_NAME}} - Test {{TEST_NUM}} Reading {{PASSAGE_LABEL_FULL}}</b></summary>

{{PASSAGE_IMAGE_BLOCKS}}

</details>

---

## 📋 Bảng Ghi Nhận Bài Làm Của Bạn (Questions {{START_Q}} – {{END_Q}})

> 💡 **Tính năng tương tác:** Nhập nhanh đáp án câu {{START_Q}} – {{END_Q}} vào các ô bên dưới (nhấn Enter hoặc Tab để nhảy câu tiếp theo). Đồng hồ đếm ngược {{TEST_TIMER}} phút hỗ trợ bám sát thời gian làm bài.

<div class="ielts-sheet-card" data-sheet-id="{{SHEET_ID}}" data-start-q="{{START_Q}}" data-end-q="{{END_Q}}" data-timer="{{TEST_TIMER}}">
  <div class="ielts-card-header">
    <div class="ielts-header-title">
      <span class="ielts-badge">Reading {{PASSAGE_LABEL_FULL}}</span>
      <span class="ielts-target-pill">{{SOURCE_NAME}} — Test {{TEST_NUM}} ({{TOTAL_QUESTIONS}} Câu)</span>
    </div>
    <div class="ielts-timer-widget">
      <span class="ielts-timer-display">{{TEST_TIMER}}:00</span>
      <div class="ielts-timer-controls">
        <button type="button" class="ielts-btn-timer ielts-btn-start" title="Bắt đầu tính giờ">▶️</button>
        <button type="button" class="ielts-btn-timer ielts-btn-pause" title="Tạm dừng" style="display:none;">⏸️</button>
        <button type="button" class="ielts-btn-timer ielts-btn-reset" title="Đặt lại đồng hồ">🔄</button>
      </div>
    </div>
  </div>

  <div class="ielts-stats-bar">
    <div class="ielts-stat-item">
      <span class="ielts-stat-label">Tiến độ:</span>
      <span class="ielts-stat-val ielts-sheet-progress">0 / {{TOTAL_QUESTIONS}} câu đã điền</span>
    </div>
    <div class="ielts-save-indicator">
      <span class="ielts-sheet-save-text">🟢 Tự động lưu LocalStorage</span>
    </div>
  </div>

  <div class="ielts-grid-answers"></div>

  <div class="ielts-card-actions">
    <button type="button" class="ielts-btn ielts-btn-primary ielts-btn-submit-ai">
      🚀 Gửi Câu Trả Lời Cho AI
    </button>
    <button type="button" class="ielts-btn ielts-btn-secondary ielts-btn-copy-shorthand">
      📋 Sao Chép Shorthand
    </button>
    <button type="button" class="ielts-btn ielts-btn-ghost ielts-btn-clear-sheet">
      🗑️ Xóa Bài Làm
    </button>
  </div>
  <div class="ielts-ai-response" style="display:none;"></div>
</div>

---

## 📊 Bảng Đối Soát Chi Tiết & Phân Tích Lỗi Sai (Questions {{START_Q}} – {{END_Q}})

{{VERIFICATION_TABLES}}

---

## 🔗 Mạng Lưới Kiến Thức Liên Quan

- 📅 **Kế hoạch cha:** [[plans/week-{{WEEK_PADDED}}/|Kế Hoạch Tuần {{WEEK_NUM}}]]
- 📖 **Phần liên quan:** [[plans/week-{{WEEK_PADDED}}/{{NEXT_PART_FILE}}|{{NEXT_PART_TITLE}}]]
- 📚 **Sổ từ vựng tuần:** [[plans/week-{{WEEK_PADDED}}/vocab-week-{{WEEK_PADDED}}|Sổ Từ Vựng Trọng Tâm Tuần {{WEEK_NUM}}]]
