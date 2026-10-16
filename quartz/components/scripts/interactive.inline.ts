function getPageSlug(): string {
  const slug = (document.body.dataset.slug || window.location.pathname)
    .replace(/^\/+|\/+$/g, "")
    .replace(/[^\w-]/g, "_");
  return slug || "root";
}

async function callApi(path: string, options: RequestInit): Promise<Response> {
  const protocol = window.location.protocol === "https:" ? "https:" : "http:";
  const hostname = window.location.hostname || "localhost";
  const primaryUrl = `${protocol}//${hostname}:8000${path}`;

  try {
    return await fetch(primaryUrl, options);
  } catch (err) {
    // Fallback: If hostname is localhost or 127.0.0.1, try the alternate loopback address
    if (hostname === "localhost") {
      const fallbackUrl = `${protocol}//127.0.0.1:8000${path}`;
      return await fetch(fallbackUrl, options);
    } else if (hostname === "127.0.0.1") {
      const fallbackUrl = `${protocol}//localhost:8000${path}`;
      return await fetch(fallbackUrl, options);
    }
    throw err;
  }
}

document.addEventListener("nav", () => {
  const slug = getPageSlug();
  const activeTimers: number[] = [];

  // Clean up any timers on navigation
  window.addCleanup(() => {
    activeTimers.forEach((t) => clearInterval(t));
  });

  // =========================================================================
  // 1. IELTS WRITING WORKSPACE
  // =========================================================================
  const writingCards = document.querySelectorAll<HTMLElement>(
    ".ielts-writing-card",
  );
  writingCards.forEach((card) => {
    const taskId = card.dataset.task || "task-1";
    const targetWords = parseInt(card.dataset.target || "150", 10);
    const initialMinutes = parseInt(card.dataset.timer || "20", 10);

    const textKey = `ielts_write_${slug}_${taskId}`;
    const timeKey = `ielts_time_${slug}_${taskId}`;

    const textarea = card.querySelector<HTMLTextAreaElement>(".ielts-textarea");
    const wordCountEl = card.querySelector<HTMLElement>(".ielts-word-count");
    const progressPillEl = card.querySelector<HTMLElement>(
      ".ielts-progress-pill",
    );
    const saveIndicatorEl = card.querySelector<HTMLElement>(".ielts-save-text");
    const timerDisplayEl = card.querySelector<HTMLElement>(
      ".ielts-timer-display",
    );
    const btnStart = card.querySelector<HTMLButtonElement>(".ielts-btn-start");
    const btnPause = card.querySelector<HTMLButtonElement>(".ielts-btn-pause");
    const btnReset = card.querySelector<HTMLButtonElement>(".ielts-btn-reset");
    const btnCopy = card.querySelector<HTMLButtonElement>(".ielts-btn-copy");
    const btnDownload = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-download",
    );
    const btnClear = card.querySelector<HTMLButtonElement>(".ielts-btn-clear");

    const cardHeader = card.querySelector<HTMLElement>(".ielts-card-header");
    if (cardHeader && !cardHeader.querySelector(".ielts-btn-split-trigger")) {
      const splitBtn = document.createElement("button");
      splitBtn.type = "button";
      splitBtn.className = "ielts-btn ielts-btn-outline ielts-btn-split-trigger";
      splitBtn.style.fontSize = "0.76rem";
      splitBtn.style.padding = "0.22rem 0.55rem";
      splitBtn.innerHTML = `🖥️ Chế độ thi 2 cột`;
      splitBtn.title = "Mở đề bài ở cột bên phải và bài làm ở cột bên trái";
      splitBtn.addEventListener("click", () => {
        document.dispatchEvent(new CustomEvent("splitscreen-open", { detail: { index: 0 } }));
      });
      cardHeader.appendChild(splitBtn);
    }

    if (!textarea) return;

    // Load saved text
    const savedText = localStorage.getItem(textKey);
    if (savedText && !textarea.value) {
      textarea.value = savedText;
    }

    // Helper: Count words
    function updateWordStats() {
      const text = textarea?.value || "";
      const words = text.trim() ? (text.match(/\b[\w'-]+\b/g) || []).length : 0;

      if (wordCountEl) {
        wordCountEl.textContent = `${words} từ`;
      }

      if (progressPillEl) {
        if (words === 0) {
          progressPillEl.textContent = `Chưa nhập bài (Mục tiêu: ≥ ${targetWords})`;
          progressPillEl.className = "ielts-progress-pill ielts-pill-neutral";
        } else if (words < targetWords) {
          progressPillEl.textContent = `⚠️ Còn thiếu ${targetWords - words} từ (${words}/${targetWords})`;
          progressPillEl.className = "ielts-progress-pill ielts-pill-warn";
        } else {
          progressPillEl.textContent = `✅ Đạt yêu cầu (${words}/${targetWords} từ)`;
          progressPillEl.className = "ielts-progress-pill ielts-pill-success";
        }
      }
    }

    updateWordStats();

    // Autosave on input (debounce)
    let saveTimeout: number | undefined;
    const onInput = () => {
      updateWordStats();
      if (saveIndicatorEl) {
        saveIndicatorEl.textContent = "Đang lưu...";
      }
      clearTimeout(saveTimeout);
      saveTimeout = window.setTimeout(() => {
        localStorage.setItem(textKey, textarea.value);
        if (saveIndicatorEl) {
          const now = new Date();
          const timeStr = now.toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });
          saveIndicatorEl.textContent = `🟢 Đã lưu vào máy (${timeStr})`;
        }
      }, 400);
    };

    textarea.addEventListener("input", onInput);
    window.addCleanup(() => textarea.removeEventListener("input", onInput));

    // Timer Logic
    let totalSeconds = initialMinutes * 60;
    let remainingSeconds = totalSeconds;
    let timerInterval: number | undefined;
    let isRunning = false;

    function formatTime(sec: number): string {
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    }

    function updateTimerDisplay() {
      if (timerDisplayEl) {
        timerDisplayEl.textContent = formatTime(remainingSeconds);
      }
    }

    updateTimerDisplay();

    function startTimer() {
      if (isRunning) return;
      isRunning = true;
      if (btnStart) btnStart.style.display = "none";
      if (btnPause) btnPause.style.display = "inline-flex";

      timerInterval = window.setInterval(() => {
        if (remainingSeconds > 0) {
          remainingSeconds--;
          updateTimerDisplay();
          sessionStorage.setItem(timeKey, String(remainingSeconds));
        } else {
          clearInterval(timerInterval);
          isRunning = false;
          if (btnStart) btnStart.style.display = "inline-flex";
          if (btnPause) btnPause.style.display = "none";
          if (timerDisplayEl) {
            timerDisplayEl.textContent = "00:00 (Hết giờ!)";
            timerDisplayEl.classList.add("ielts-timer-alert");
          }
        }
      }, 1000);
      activeTimers.push(timerInterval);
    }

    function pauseTimer() {
      if (!isRunning) return;
      isRunning = false;
      clearInterval(timerInterval);
      if (btnStart) btnStart.style.display = "inline-flex";
      if (btnPause) btnPause.style.display = "none";
    }

    function resetTimer() {
      pauseTimer();
      remainingSeconds = totalSeconds;
      updateTimerDisplay();
      sessionStorage.removeItem(timeKey);
      if (timerDisplayEl) {
        timerDisplayEl.classList.remove("ielts-timer-alert");
      }
    }

    btnStart?.addEventListener("click", startTimer);
    btnPause?.addEventListener("click", pauseTimer);
    btnReset?.addEventListener("click", resetTimer);

    // Copy to AI
    btnCopy?.addEventListener("click", () => {
      const text = textarea.value.trim();
      if (!text) {
        alert("Khung bài làm đang trống! Hãy viết bài trước khi sao chép.");
        return;
      }

      const words = (text.match(/\b[\w'-]+\b/g) || []).length;
      const spentSec = totalSeconds - remainingSeconds;
      const spentMin = Math.floor(spentSec / 60);
      const spentSecRemainder = spentSec % 60;
      const spentStr = `${spentMin} phút ${spentSecRemainder} giây`;

      const promptPayload = [
        `=== 📝 BÀI LÀM IELTS WRITING CẦN CHẤM & GÓP Ý ===`,
        `• Tài liệu: ${document.title}`,
        `• Phần thi: ${card.querySelector(".ielts-badge")?.textContent || taskId.toUpperCase()}`,
        `• Số từ thực tế: ${words} từ (Mục tiêu: ≥ ${targetWords} từ)`,
        `• Thời gian hoàn thành: ${spentStr}`,
        `\n--- NỘI DUNG BÀI VIẾT ---\n`,
        text,
        `\n------------------------`,
        `👉 Nhờ bạn đối soát, nhận xét theo 4 tiêu chí chấm điểm IELTS Writing (TR/TA, CC, LR, GRA) và gợi ý các cụm từ nâng cấp tự nhiên!`,
      ].join("\n");

      navigator.clipboard.writeText(promptPayload).then(() => {
        const origText = btnCopy.textContent;
        btnCopy.textContent = "✅ Đã Sao Chép! Hãy dán vào chat";
        btnCopy.classList.add("ielts-btn-success");
        setTimeout(() => {
          btnCopy.textContent = origText;
          btnCopy.classList.remove("ielts-btn-success");
        }, 3000);
      });
    });

    // Download .md file
    btnDownload?.addEventListener("click", () => {
      const text = textarea.value.trim();
      if (!text) {
        alert("Khung bài làm đang trống!");
        return;
      }
      const words = (text.match(/\b[\w'-]+\b/g) || []).length;
      const mdContent = `# Bài Làm IELTS Writing - ${taskId.toUpperCase()}\n\n- **Ngày làm:** ${new Date().toLocaleDateString("vi-VN")}\n- **Số từ:** ${words} từ\n\n---\n\n${text}\n`;
      const blob = new Blob([mdContent], {
        type: "text/markdown;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ielts-writing-${taskId}.md`;
      a.click();
      URL.revokeObjectURL(url);
    });

    // Clear and reset
    btnClear?.addEventListener("click", () => {
      if (confirm("Bạn có chắc chắn muốn xóa bài làm này để làm lại từ đầu?")) {
        textarea.value = "";
        localStorage.removeItem(textKey);
        resetTimer();
        updateWordStats();
        if (saveIndicatorEl) {
          saveIndicatorEl.textContent = "Đã làm mới khung bài làm.";
        }
      }
    });

    // -----------------------------------------------------------------------
    // AI Submission Directly for Writing
    // -----------------------------------------------------------------------
    const cardActions = card.querySelector<HTMLElement>(".ielts-card-actions");
    let btnSubmit = card.querySelector<HTMLButtonElement>(".ielts-btn-submit-ai");
    if (!btnSubmit && cardActions) {
      btnSubmit = document.createElement("button");
      btnSubmit.type = "button";
      btnSubmit.className = "ielts-btn ielts-btn-primary ielts-btn-submit-ai";
      btnSubmit.innerHTML = `🚀 Gửi Bài Viết Cho AI`;
      cardActions.insertBefore(btnSubmit, cardActions.firstChild);
    }

    let aiResponseContainer = card.querySelector<HTMLElement>(".ielts-ai-response");
    if (!aiResponseContainer) {
      aiResponseContainer = document.createElement("div");
      aiResponseContainer.className = "ielts-ai-response";
      aiResponseContainer.style.display = "none";
      card.appendChild(aiResponseContainer);
    }

    btnSubmit?.addEventListener("click", async () => {
      const text = textarea.value.trim();
      if (!text) {
        alert("Khung bài làm đang trống! Hãy viết bài trước khi gửi cho AI.");
        return;
      }

      const origHtml = btnSubmit!.innerHTML;
      btnSubmit!.disabled = true;
      btnSubmit!.innerHTML = `⏳ Đang gửi cho AI đọc bài...`;

      try {
        const response = await callApi("/api/v1/agents/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            attempt_text: text,
            skill: "writing",
            source_file: window.location.pathname,
          }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Lỗi HTTP ${response.status}`);
        }

        const result = await response.json();

        // Inform parent SPA window if present
        if (window.parent && window.parent !== window) {
          const words = (text.match(/\b[\w'-]+\b/g) || []).length;
          window.parent.postMessage(
            {
              type: "IELTS_TEST_SUBMITTED",
              payload: {
                skill: "writing",
                filledCount: words,
              },
            },
            "*",
          );
        }

        // Render AI Result Box inside note
        if (aiResponseContainer) {
          const words = (text.match(/\b[\w'-]+\b/g) || []).length;
          const drills = result.recommended_drills || [];
          aiResponseContainer.innerHTML = `
            <div class="ielts-ai-banner ielts-ai-banner-success">
              <span style="font-size: 1.5rem;">🎉</span>
              <div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #2e7d32;">AI Đã Tiếp Nhận Bài Viết Thành Công</div>
                <div style="font-size: 0.82rem; margin-top: 3px;">
                  Độ dài: <strong>${words} từ</strong> &bull; Trạng thái: <strong>Đã ghi nhận bài làm vào hệ thống PKM</strong>
                </div>
              </div>
            </div>
            ${result.feedback ? `<div class="ielts-ai-feedback-box" style="margin-top: 0.75rem; padding: 0.85rem; background: var(--light); border: 1px solid var(--lightgray); border-radius: 8px; font-size: 0.85rem; line-height: 1.5;">${result.feedback}</div>` : ""}
            ${
              drills.length > 0
                ? `
              <div class="ielts-ai-drills" style="margin-top: 0.75rem;">
                <div style="font-weight: 700; margin-bottom: 0.35rem; color: var(--dark);">🎯 Hướng dẫn & Đề xuất Micro-session:</div>
                <ul style="margin: 0; padding-left: 1.2rem; color: var(--darkgray);">
                  ${drills.map((d: string) => `<li>${d}</li>`).join("")}
                </ul>
              </div>`
                : ""
            }
            <div style="margin-top: 0.75rem; display: flex; justify-content: flex-end;">
              <button type="button" class="ielts-btn ielts-btn-ghost ielts-btn-close-ai" style="font-size: 0.75rem;">
                Thu gọn kết quả ▲
              </button>
            </div>
          `;
          aiResponseContainer.style.display = "block";
          aiResponseContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });

          const btnClose = aiResponseContainer.querySelector(".ielts-btn-close-ai");
          btnClose?.addEventListener("click", () => {
            if (aiResponseContainer) aiResponseContainer.style.display = "none";
          });
        }
      } catch (err: any) {
        console.error("Lỗi AI Evaluator (Writing):", err);
        const msg = err.message || String(err);
        if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
          alert(`Không thể kết nối tới AI Evaluator: Không thể kết nối tới máy chủ backend tại cổng 8000. Vui lòng kiểm tra Docker hoặc dịch vụ FastAPI.`);
        } else {
          alert(`Không thể kết nối tới AI Evaluator: ${msg}`);
        }
      } finally {
        btnSubmit!.disabled = false;
        btnSubmit!.innerHTML = origHtml;
      }
    });
  });

  // =========================================================================
  // 2. IELTS INTERACTIVE ANSWER SHEET (Reading & Listening)
  // =========================================================================
  const sheetCards =
    document.querySelectorAll<HTMLElement>(".ielts-sheet-card");
  sheetCards.forEach((card) => {
    const sheetId = card.dataset.sheetId || "sheet-1";
    const startQ = parseInt(card.dataset.startQ || "1", 10);
    const endQ = parseInt(card.dataset.endQ || "40", 10);
    const storageKey = `ielts_sheet_${slug}_${sheetId}`;

    const gridContainer = card.querySelector<HTMLElement>(
      ".ielts-grid-answers",
    );
    const progressEl = card.querySelector<HTMLElement>(".ielts-sheet-progress");
    const saveIndicatorEl = card.querySelector<HTMLElement>(
      ".ielts-sheet-save-text",
    );
    const btnCopy = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-copy-shorthand",
    );
    const btnClear = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-clear-sheet",
    );

    const cardHeader = card.querySelector<HTMLElement>(".ielts-card-header");
    if (cardHeader && !cardHeader.querySelector(".ielts-btn-split-trigger")) {
      const splitBtn = document.createElement("button");
      splitBtn.type = "button";
      splitBtn.className = "ielts-btn ielts-btn-outline ielts-btn-split-trigger";
      splitBtn.style.fontSize = "0.76rem";
      splitBtn.style.padding = "0.22rem 0.55rem";
      splitBtn.innerHTML = `🖥️ Chế độ thi 2 cột`;
      splitBtn.title = "Mở đề bài ở cột bên phải và bảng điền đáp án ở cột bên trái";
      splitBtn.addEventListener("click", () => {
        document.dispatchEvent(new CustomEvent("splitscreen-open", { detail: { index: 0 } }));
      });
      cardHeader.appendChild(splitBtn);
    }

    if (!gridContainer) return;

    // Render cells if empty
    if (!gridContainer.children.length) {
      const fragment = document.createDocumentFragment();
      for (let q = startQ; q <= endQ; q++) {
        const cell = document.createElement("div");
        cell.className = "ielts-q-cell";
        cell.innerHTML = `
          <span class="ielts-q-num">${q}</span>
          <input type="text" class="ielts-q-input" data-q="${q}" placeholder="..." autocomplete="off" spellcheck="false" />
        `;
        fragment.appendChild(cell);
      }
      gridContainer.appendChild(fragment);
    }

    const inputs = card.querySelectorAll<HTMLInputElement>(".ielts-q-input");

    // Load saved answers
    let answers: Record<string, string> = {};
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) answers = JSON.parse(raw);
    } catch (e) {}

    inputs.forEach((input) => {
      const q = input.dataset.q!;
      if (answers[q]) {
        input.value = answers[q];
      }
    });

    function updateProgress() {
      let filled = 0;
      inputs.forEach((i) => {
        if (i.value.trim()) filled++;
      });
      const total = endQ - startQ + 1;
      if (progressEl) {
        progressEl.textContent = `${filled} / ${total} câu đã điền`;
      }
    }

    updateProgress();

    // Handle input change & enter navigation
    inputs.forEach((input, idx) => {
      input.addEventListener("input", () => {
        const q = input.dataset.q!;
        answers[q] = input.value.trim();
        localStorage.setItem(storageKey, JSON.stringify(answers));
        updateProgress();
        if (saveIndicatorEl) {
          saveIndicatorEl.textContent = "🟢 Đã lưu vào máy";
        }
      });

      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === "Tab") {
          e.preventDefault();
          const next = inputs[idx + 1];
          if (next) {
            next.focus();
            next.select();
          }
        }
      });
    });

    // -----------------------------------------------------------------------
    // AI Submission Directly from Note (No tab-switching required)
    // -----------------------------------------------------------------------
    const cardActions = card.querySelector<HTMLElement>(".ielts-card-actions");
    let btnSubmit = card.querySelector<HTMLButtonElement>(".ielts-btn-submit-ai");
    if (!btnSubmit && cardActions) {
      btnSubmit = document.createElement("button");
      btnSubmit.type = "button";
      btnSubmit.className = "ielts-btn ielts-btn-primary ielts-btn-submit-ai";
      btnSubmit.innerHTML = `🚀 Gửi Câu Trả Lời Cho AI`;
      cardActions.insertBefore(btnSubmit, cardActions.firstChild);
    }

    let aiResponseContainer = card.querySelector<HTMLElement>(".ielts-ai-response");
    if (!aiResponseContainer) {
      aiResponseContainer = document.createElement("div");
      aiResponseContainer.className = "ielts-ai-response";
      aiResponseContainer.style.display = "none";
      card.appendChild(aiResponseContainer);
    }

    btnSubmit?.addEventListener("click", async () => {
      const lines: string[] = [];
      let filledCount = 0;

      for (let q = startQ; q <= endQ; q++) {
        const val = (answers[String(q)] || "").trim();
        if (val) {
          lines.push(`${q} ${val}`);
          filledCount++;
        }
      }

      if (filledCount === 0) {
        alert("Bảng đáp án đang trống! Hãy điền câu trả lời trước khi gửi cho AI.");
        return;
      }

      const origText = btnSubmit.innerHTML;
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = `⏳ Đang gửi cho AI đọc...`;

      const badgeText = card.querySelector(".ielts-badge")?.textContent?.toLowerCase() || "";
      const skill = badgeText.includes("reading") ? "reading" : "listening";

      try {
        const response = await callApi("/api/v1/agents/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            attempt_text: lines.join("\n"),
            skill: skill,
            source_file: window.location.pathname,
          }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Lỗi HTTP ${response.status}`);
        }

        const result = await response.json();

        // Render AI Result Box inside note
        if (aiResponseContainer) {
          const totalQ = endQ - startQ + 1;
          const questionsList = result.questions || [];

          aiResponseContainer.innerHTML = `
            ${
              result.score_fraction
                ? `
              <div class="ielts-ai-banner ielts-ai-banner-success">
                <span style="font-size: 1.5rem;">🎉</span>
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: #2e7d32;">Kết Quả Chấm Điểm Chính Thức</div>
                  <div style="font-size: 0.82rem; margin-top: 3px;">
                    <strong>${result.score_fraction} câu đúng</strong> &bull; Band Score: <strong style="color: #007aff; font-size: 1rem;">${result.band_score}</strong>
                  </div>
                </div>
              </div>`
                : `
              <div class="ielts-ai-banner ielts-ai-banner-info">
                <span style="font-size: 1.5rem;">🛡️</span>
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: #007aff;">Nguyên Tắc Vàng: Lưu Trữ Trung Thực Bài Làm</div>
                  <div style="font-size: 0.82rem; margin-top: 3px; color: var(--darkgray);">
                    Hệ thống đã lưu trữ trung thực <strong>${filledCount}/${totalQ} câu trả lời</strong> của bạn. AI <strong>tuyệt đối không tự suy đoán điểm số</strong> khi bạn chưa cung cấp bảng đáp án chính thức.
                  </div>
                </div>
              </div>`
            }

            <div class="ielts-ai-table-wrap">
              <table class="ielts-ai-table">
                <thead>
                  <tr>
                    <th style="width: 50px; text-align: center;">Câu</th>
                    <th>Đáp Án Của Bạn</th>
                    <th style="width: 120px;">Trạng Thái</th>
                    <th>Ghi Chú Phân Tích</th>
                  </tr>
                </thead>
                <tbody>
                  ${questionsList
                    .map(
                      (q: any) => `
                    <tr>
                      <td style="font-weight: 700; text-align: center;">${q.question_number}</td>
                      <td style="font-family: monospace; font-weight: 600;">${
                        q.user_answer ||
                        '<span style="color:#8e8e93; font-style:italic;">(bỏ trống)</span>'
                      }</td>
                      <td>
                        ${
                          q.is_correct === true
                            ? '<span style="color:#34c759; font-weight:700;">✅ Đúng</span>'
                            : q.is_correct === false
                              ? '<span style="color:#ff3b30; font-weight:700;">❌ Sai</span>'
                              : '<span style="color:#8e8e93; font-style:italic;">⚪ Đã ghi nhận</span>'
                        }
                      </td>
                      <td style="color: var(--darkgray); font-size: 0.78rem;">${
                        q.trap_type || q.explanation || "—"
                      }</td>
                    </tr>
                  `,
                    )
                    .join("")}
                </tbody>
              </table>
            </div>

            ${
              result.recommended_drills && result.recommended_drills.length > 0
                ? `
              <div class="ielts-ai-drills">
                <div style="font-weight: 700; margin-bottom: 0.35rem; color: var(--dark);">🎯 Bài tập Micro-Session đề xuất (30–35 phút):</div>
                <ul style="margin: 0; padding-left: 1.2rem; color: var(--darkgray);">
                  ${result.recommended_drills
                    .map((d: string) => `<li>${d}</li>`)
                    .join("")}
                </ul>
              </div>`
                : ""
            }

            <div style="margin-top: 0.75rem; display: flex; justify-content: flex-end;">
              <button type="button" class="ielts-btn ielts-btn-ghost ielts-btn-close-ai" style="font-size: 0.75rem;">
                Thu gọn kết quả ▲
              </button>
            </div>
          `;

          aiResponseContainer.style.display = "block";
          aiResponseContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });

          const btnClose = aiResponseContainer.querySelector(".ielts-btn-close-ai");
          btnClose?.addEventListener("click", () => {
            if (aiResponseContainer) aiResponseContainer.style.display = "none";
          });
        }

        btnSubmit.innerHTML = `✅ Đã Gửi Thành Công!`;
        btnSubmit.classList.add("ielts-btn-success");

        // Gửi thông điệp cho parent React SPA
        if (window.parent && window.parent !== window) {
          window.parent.postMessage(
            {
              type: "IELTS_TEST_SUBMITTED",
              payload: {
                skill,
                filledCount,
                result,
              },
            },
            "*",
          );
        }

        setTimeout(() => {
          btnSubmit.innerHTML = origText;
          btnSubmit.disabled = false;
          btnSubmit.classList.remove("ielts-btn-success");
        }, 4000);
      } catch (err: any) {
        console.error("Lỗi gửi bài cho AI:", err);
        const msg = err.message || String(err);
        if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
          alert(`Không thể kết nối tới AI Evaluator: Không thể kết nối tới máy chủ backend tại cổng 8000. Vui lòng kiểm tra Docker hoặc dịch vụ FastAPI.`);
        } else {
          alert(`Không thể gửi bài làm cho AI: ${msg}`);
        }
        btnSubmit.innerHTML = origText;
        btnSubmit.disabled = false;
      }
    });

    // Copy Shorthand for AI
    btnCopy?.addEventListener("click", () => {
      const lines: string[] = [];
      let filledCount = 0;

      for (let q = startQ; q <= endQ; q++) {
        const val = answers[String(q)] || "";
        if (val) {
          lines.push(`${q} ${val}`);
          filledCount++;
        }
      }

      if (filledCount === 0) {
        alert(
          "Bảng đáp án đang trống! Hãy điền câu trả lời trước khi sao chép.",
        );
        return;
      }

      const promptPayload = [
        `=== 📋 BÀI LÀM ĐÁP ÁN (SHORTHAND) ===`,
        `• Tài liệu: ${document.title}`,
        `• Phần thi: ${card.querySelector(".ielts-badge")?.textContent || sheetId}`,
        `• Tiến độ: ${filledCount} / ${endQ - startQ + 1} câu`,
        `\n--- BẢNG ĐÁP ÁN CỦA BẠN ---\n`,
        lines.join("\n"),
        `\n---------------------------`,
        `👉 Nhờ bạn lưu trữ bài làm này vào bảng đối soát của hệ thống!`,
      ].join("\n");

      navigator.clipboard.writeText(promptPayload).then(() => {
        const origText = btnCopy.textContent;
        btnCopy.textContent = "✅ Đã Sao Chép Shorthand!";
        btnCopy.classList.add("ielts-btn-success");
        setTimeout(() => {
          btnCopy.textContent = origText;
          btnCopy.classList.remove("ielts-btn-success");
        }, 3000);
      });
    });

    // Clear answers
    btnClear?.addEventListener("click", () => {
      if (
        confirm("Bạn có chắc chắn muốn xóa toàn bộ câu trả lời trong bảng này?")
      ) {
        inputs.forEach((i) => (i.value = ""));
        answers = {};
        localStorage.removeItem(storageKey);
        updateProgress();
        if (saveIndicatorEl) {
          saveIndicatorEl.textContent = "Đã xóa sạch đáp án.";
        }
      }
    });
  });
});
