function getPageSlug(): string {
  const slug = (document.body.dataset.slug || window.location.pathname)
    .replace(/^\/+|\/+$/g, "")
    .replace(/[^\w-]/g, "_");
  return slug || "root";
}

async function callApi(path: string, options: RequestInit): Promise<Response> {
  const protocol = window.location.protocol === "https:" ? "https:" : "http:";
  const hostname = window.location.hostname || "localhost";
  const port = window.location.port;

  // Xây dựng danh sách URL ứng viên theo thứ tự ưu tiên thông minh:
  const candidates: string[] = [];

  // 1. Relative path trực tiếp (chuẩn nhất khi chạy qua Cloudflare Tunnel / Reverse Proxy)
  candidates.push(path);

  // 2. Cổng web chuẩn (port 80 / 443) trên cùng hostname (khi Quartz nằm trong iframe)
  if (port && port !== "80" && port !== "443" && port !== "8000") {
    candidates.push(`${protocol}//${hostname}${path}`);
  }

  // 3. Cổng 8000 trực tiếp (dành cho môi trường local dev độc lập)
  candidates.push(`${protocol}//${hostname}:8000${path}`);

  // 4. Fallback loopback cho localhost / 127.0.0.1
  if (hostname === "localhost") {
    candidates.push(`${protocol}//127.0.0.1:8000${path}`);
  } else if (hostname === "127.0.0.1") {
    candidates.push(`${protocol}//localhost:8000${path}`);
  }

  let lastError: any = null;
  for (const url of candidates) {
    try {
      const res = await fetch(url, options);
      return res;
    } catch (err) {
      lastError = err;
      continue;
    }
  }

  throw lastError || new Error("Không thể kết nối đến máy chủ backend.");
}

async function copyToClipboard(text: string): Promise<boolean> {
  // 1. Thử dùng Clipboard API hiện đại nếu môi trường hỗ trợ (HTTPS / Localhost)
  if (navigator?.clipboard && typeof navigator.clipboard.writeText === "function") {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      console.warn("navigator.clipboard.writeText bị từ chối, chuyển sang execCommand fallback:", e);
    }
  }

  // 2. Fallback đáng tin cậy với textarea ẩn + execCommand('copy') cho HTTP / iframe / Direct IP
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.top = "0";
    textArea.style.left = "-9999px";
    textArea.style.opacity = "0";
    textArea.setAttribute("readonly", "");
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    const successful = document.execCommand("copy");
    textArea.remove();
    return successful;
  } catch (err) {
    console.error("Lỗi khi sao chép clipboard:", err);
    return false;
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
      splitBtn.className =
        "ielts-btn ielts-btn-outline ielts-btn-split-trigger";
      splitBtn.style.fontSize = "0.76rem";
      splitBtn.style.padding = "0.22rem 0.55rem";
      splitBtn.innerHTML = `🖥️ Chế độ thi 2 cột`;
      splitBtn.title = "Mở đề bài ở cột bên phải và bài làm ở cột bên trái";
      splitBtn.addEventListener("click", () => {
        (document as any).dispatchEvent(
          new CustomEvent("splitscreen-open", { detail: { index: 0 } }),
        );
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

      copyToClipboard(promptPayload).then((success) => {
        if (!success) {
          alert("Không thể tự động sao chép. Hãy chọn bài làm và sao chép thủ công.");
          return;
        }
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
    let btnSubmit = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-submit-ai",
    );
    if (!btnSubmit && cardActions) {
      btnSubmit = document.createElement("button");
      btnSubmit.type = "button";
      btnSubmit.className = "ielts-btn ielts-btn-primary ielts-btn-submit-ai";
      btnSubmit.innerHTML = `🚀 Gửi Bài Viết Cho AI`;
      cardActions.insertBefore(btnSubmit, cardActions.firstChild);
    }

    let aiResponseContainer =
      card.querySelector<HTMLElement>(".ielts-ai-response");
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
            task_id: taskId,
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
          const editsCount = result.edits_count ?? 0;
          const hasDiff = Boolean(result.diff_html);

          let diffContentHtml = "";
          if (hasDiff) {
            diffContentHtml = `
              <div class="ielts-diff-tab-bar">
                <button type="button" class="ielts-diff-tab-btn active" data-tab="diff">
                  🔴🟢 Bản Sửa Trực Quan (${editsCount} điểm sửa)
                </button>
                <button type="button" class="ielts-diff-tab-btn" data-tab="clean">
                  🌟 Bản Viết Lại Hoàn Chỉnh
                </button>
                <button type="button" class="ielts-diff-tab-btn" data-tab="rubric">
                  📊 Nhận Xét 4 Tiêu Chí IELTS
                </button>
              </div>

              <div class="ielts-diff-panel ielts-diff-panel-diff">
                <div class="ielts-diff-view-content">
                  ${result.diff_html}
                </div>
              </div>

              <div class="ielts-diff-panel ielts-diff-panel-clean" style="display: none;">
                <div class="ielts-diff-clean-box">${result.clean_rewritten_text || ""}</div>
              </div>

              <div class="ielts-diff-panel ielts-diff-panel-rubric" style="display: none;">
                ${result.feedback ? `<div class="ielts-ai-feedback-box" style="padding: 0.85rem; background: var(--light); border: 1px solid var(--lightgray); border-radius: 8px; font-size: 0.85rem; line-height: 1.6; white-space: pre-line;"><div>${result.feedback}</div></div>` : ""}
              </div>
            `;
          } else if (result.feedback) {
            diffContentHtml = `
              <div class="ielts-ai-feedback-box" style="margin-top: 0.75rem; padding: 0.85rem; background: var(--light); border: 1px solid var(--lightgray); border-radius: 8px; font-size: 0.85rem; line-height: 1.6; white-space: pre-line;"><div style="font-weight:700; color:var(--secondary); margin-bottom:0.35rem;">💡 Nhận Xét & Đánh Giá 4 Tiêu Chí Từ AI:</div><div>${result.feedback}</div></div>
            `;
          }

          aiResponseContainer.innerHTML = `
            <div class="ielts-ai-banner ielts-ai-banner-success">
              <span style="font-size: 1.5rem;">🎉</span>
              <div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #2e7d32;">AI Đã Tiếp Nhận & Sửa Bài Viết Thành Công</div>
                <div style="font-size: 0.82rem; margin-top: 3px;">
                  Độ dài: <strong>${words} từ</strong> &bull; Điểm cải thiện: <strong>${editsCount} cụm từ nâng cấp</strong>
                </div>
                ${result.updated_file ? `<div style="margin-top: 4px; font-size: 0.8rem; color: #15803d; font-weight: 600;">📁 Đã đồng bộ vào: <code>${result.updated_file}</code></div>` : ""}
              </div>
            </div>
            
            ${diffContentHtml}

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
          aiResponseContainer.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
          });

          // Bind tab click events
          const tabButtons = aiResponseContainer.querySelectorAll<HTMLButtonElement>(".ielts-diff-tab-btn");
          const panels = aiResponseContainer.querySelectorAll<HTMLElement>(".ielts-diff-panel");
          tabButtons.forEach((tabBtn) => {
            tabBtn.addEventListener("click", () => {
              const tab = tabBtn.dataset.tab;
              tabButtons.forEach((b) => b.classList.remove("active"));
              tabBtn.classList.add("active");
              panels.forEach((p) => {
                if (p.classList.contains(`ielts-diff-panel-${tab}`)) {
                  p.style.display = "block";
                } else {
                  p.style.display = "none";
                }
              });
            });
          });

          const btnClose = aiResponseContainer.querySelector(
            ".ielts-btn-close-ai",
          );
          btnClose?.addEventListener("click", () => {
            if (aiResponseContainer) aiResponseContainer.style.display = "none";
          });
        }
      } catch (err: any) {
        console.error("Lỗi AI Evaluator (Writing):", err);
        const msg = err.message || String(err);
        if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
          alert(
            `Không thể kết nối tới AI Evaluator: Không thể kết nối tới máy chủ backend. Vui lòng kiểm tra dịch vụ FastAPI hoặc kết nối mạng.`,
          );
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
    const initialMinutes = parseInt(card.dataset.timer || "30", 10);
    const storageKey = `ielts_sheet_${slug}_${sheetId}`;
    const timeKey = `ielts_time_${slug}_${sheetId}`;

    const gridContainer = card.querySelector<HTMLElement>(
      ".ielts-grid-answers, .ielts-grid-container",
    );
    const progressEl = card.querySelector<HTMLElement>(
      ".ielts-sheet-progress, .ielts-progress-count, .ielts-progress-text",
    );
    const saveIndicatorEl = card.querySelector<HTMLElement>(
      ".ielts-sheet-save-text, .ielts-status-indicator, .ielts-save-text",
    );
    const timerDisplayEl = card.querySelector<HTMLElement>(
      ".ielts-timer-display",
    );
    const btnStart = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-start, .ielts-btn-timer.ielts-btn-start",
    );
    const btnPause = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-pause, .ielts-btn-timer.ielts-btn-pause",
    );
    const btnReset = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-reset, .ielts-btn-timer.ielts-btn-reset",
    );
    const btnCopy = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-copy-shorthand, .ielts-btn-copy",
    );
    const btnClear = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-clear-sheet, .ielts-btn-clear",
    );

    // Timer logic for answer sheet
    let totalSeconds = initialMinutes * 60;
    let remainingSeconds = totalSeconds;
    let timerInterval: number | undefined;
    let isRunning = false;

    try {
      const savedTimer = sessionStorage.getItem(timeKey);
      if (savedTimer && !isNaN(parseInt(savedTimer, 10))) {
        remainingSeconds = parseInt(savedTimer, 10);
      }
    } catch (e) {}

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

    const cardHeader = card.querySelector<HTMLElement>(".ielts-card-header");
    if (cardHeader && !cardHeader.querySelector(".ielts-btn-split-trigger")) {
      const splitBtn = document.createElement("button");
      splitBtn.type = "button";
      splitBtn.className =
        "ielts-btn ielts-btn-outline ielts-btn-split-trigger";
      splitBtn.style.fontSize = "0.76rem";
      splitBtn.style.padding = "0.22rem 0.55rem";
      splitBtn.innerHTML = `🖥️ Chế độ thi 2 cột`;
      splitBtn.title =
        "Mở đề bài ở cột bên phải và bảng điền đáp án ở cột bên trái";
      splitBtn.addEventListener("click", () => {
        (document as any).dispatchEvent(
          new CustomEvent("splitscreen-open", { detail: { index: 0 } }),
        );
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
    let btnSubmit = card.querySelector<HTMLButtonElement>(
      ".ielts-btn-submit-ai",
    );
    if (!btnSubmit && cardActions) {
      btnSubmit = document.createElement("button");
      btnSubmit.type = "button";
      btnSubmit.className = "ielts-btn ielts-btn-primary ielts-btn-submit-ai";
      btnSubmit.innerHTML = `🚀 Gửi Câu Trả Lời Cho AI`;
      cardActions.insertBefore(btnSubmit, cardActions.firstChild);
    }

    let aiResponseContainer =
      card.querySelector<HTMLElement>(".ielts-ai-response");
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
        alert(
          "Bảng đáp án đang trống! Hãy điền câu trả lời trước khi gửi cho AI.",
        );
        return;
      }

      const origText = btnSubmit.innerHTML;
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = `⏳ Đang gửi cho AI đọc...`;

      const badgeText =
        card.querySelector(".ielts-badge")?.textContent?.toLowerCase() || "";
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
                  <div style="font-weight: 700; font-size: 0.95rem; color: #2e7d32;">Kết Quả Chấm Điểm Trực Tiếp (Cambridge 18)</div>
                  <div style="font-size: 0.82rem; margin-top: 3px;">
                    <strong>${result.score_fraction} câu đúng</strong> &bull; Band Score: <strong style="color: #007aff; font-size: 1rem;">${result.band_score}</strong>
                  </div>
                  ${result.updated_file ? `<div style="margin-top: 4px; font-size: 0.8rem; color: #15803d; font-weight: 600;">📁 Đã cập nhật Bảng Đối Soát trong: <code>${result.updated_file}</code></div>` : ""}
                </div>
              </div>`
                : `
              <div class="ielts-ai-banner ielts-ai-banner-info">
                <span style="font-size: 1.5rem;">🛡️</span>
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: #007aff;">Nguyên Tắc Vàng: Lưu Trữ Trung Thực Bài Làm</div>
                  <div style="font-size: 0.82rem; margin-top: 3px; color: var(--darkgray);">
                    Hệ thống đã lưu trữ trung thực <strong>${filledCount}/${totalQ} câu trả lời</strong> của bạn vào Bảng Đối Soát Bài Làm. AI <strong>tuyệt đối không tự suy đoán điểm số</strong> khi bạn chưa cung cấp bảng đáp án chính thức.
                  </div>
                  ${result.updated_file ? `<div style="margin-top: 4px; font-size: 0.8rem; color: #15803d; font-weight: 600;">📁 Đã đồng bộ vào: <code>${result.updated_file}</code></div>` : ""}
                </div>
              </div>`
            }

            ${
              result.feedback
                ? `
              <div class="ielts-ai-feedback-box" style="margin-top: 0.75rem; padding: 0.85rem; background: var(--light); border: 1px solid var(--lightgray); border-radius: 8px; font-size: 0.85rem; line-height: 1.6; white-space: pre-line;">
                <div style="font-weight: 700; color: var(--secondary); margin-bottom: 0.35rem;">💡 Nhận Xét & Chẩn Đoán Lỗi Sai Từ AI:</div>
                <div>${result.feedback}</div>
              </div>`
                : ""
            }

            <div class="ielts-ai-table-wrap">
              <table class="ielts-ai-table">
                <thead>
                  <tr>
                    <th style="width: 45px; text-align: center;">Câu</th>
                    <th>Đáp Án Của Bạn</th>
                    <th>Đáp Án Chuẩn</th>
                    <th style="width: 100px; text-align: center;">Trạng Thái</th>
                    <th>Giải Thích & Bẫy Đề Thi</th>
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
                      <td style="font-family: monospace; font-weight: 700; color: var(--secondary);">${
                        q.correct_answer || '<span style="color:#8e8e93; font-style:italic;">—</span>'
                      }</td>
                      <td style="text-align: center;">
                        ${
                          q.is_correct === true
                            ? '<span style="color:#34c759; font-weight:700;">✅ Đúng</span>'
                            : q.is_correct === false
                              ? '<span style="color:#ff3b30; font-weight:700;">❌ Sai</span>'
                              : '<span style="color:#8e8e93; font-style:italic;">⚪ Đã ghi nhận</span>'
                        }
                      </td>
                      <td style="color: var(--darkgray); font-size: 0.78rem;">${
                        (q.trap_type ? `<strong>[${q.trap_type}]</strong> ` : '') + (q.explanation || "—")
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

          // Live DOM Table Synchronization: Cập nhật trực tiếp vào bảng trên trang ghi chú
          const tables = document.querySelectorAll<HTMLTableElement>("table");
          tables.forEach((tbl) => {
            if (tbl.closest(".ielts-ai-table-wrap")) return;
            const rows = tbl.querySelectorAll<HTMLTableRowElement>("tbody tr");
            rows.forEach((row) => {
              const firstCell = row.cells[0]?.textContent
                ?.replace(/\*/g, "")
                .trim();
              if (firstCell && /^\d+$/.test(firstCell)) {
                const qNum = parseInt(firstCell, 10);
                const qData = questionsList.find(
                  (q: any) => q.question_number === qNum,
                );
                if (qData) {
                  if (row.cells[1] && qData.user_answer) {
                    row.cells[1].innerHTML = `<code style="font-weight:700; color:var(--secondary);">${qData.user_answer}</code>`;
                  }
                  if (row.cells.length >= 5) {
                    if (qData.correct_answer && row.cells[2]) {
                      row.cells[2].textContent = qData.correct_answer;
                    }
                    if (row.cells[3]) {
                      row.cells[3].innerHTML =
                        qData.is_correct === true
                          ? '<span style="color:#34c759;font-weight:700;">✅</span>'
                          : qData.is_correct === false
                            ? '<span style="color:#ff3b30;font-weight:700;">❌</span>'
                            : '<span style="color:#8e8e93;">⚪</span>';
                    }
                    if (
                      row.cells[4] &&
                      (qData.trap_type || qData.explanation)
                    ) {
                      row.cells[4].textContent =
                        `${qData.trap_type || ""}: ${qData.explanation || ""}`.replace(
                          /^:\s*/,
                          "",
                        );
                    }
                  } else if (row.cells.length === 4) {
                    if (row.cells[2]) {
                      row.cells[2].innerHTML =
                        qData.is_correct === true
                          ? "✅"
                          : qData.is_correct === false
                            ? "❌"
                            : "[x]";
                    }
                    if (
                      row.cells[3] &&
                      (qData.trap_type || qData.explanation)
                    ) {
                      row.cells[3].textContent =
                        `${qData.trap_type || ""}: ${qData.explanation || ""}`.replace(
                          /^:\s*/,
                          "",
                        );
                    }
                  }
                }
              }
            });
          });

          aiResponseContainer.style.display = "block";
          aiResponseContainer.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
          });

          const btnClose = aiResponseContainer.querySelector(
            ".ielts-btn-close-ai",
          );
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
          alert(
            `Không thể kết nối tới AI Evaluator: Không thể kết nối tới máy chủ backend. Vui lòng kiểm tra dịch vụ FastAPI hoặc kết nối mạng.`,
          );
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

      copyToClipboard(promptPayload).then((success) => {
        if (!success) {
          alert("Không thể tự động sao chép. Hãy chọn nội dung và sao chép thủ công.");
          return;
        }
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
