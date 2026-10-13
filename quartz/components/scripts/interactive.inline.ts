function getPageSlug(): string {
  const slug = (document.body.dataset.slug || window.location.pathname)
    .replace(/^\/+|\/+$/g, "")
    .replace(/[^\w-]/g, "_")
  return slug || "root"
}

document.addEventListener("nav", () => {
  const slug = getPageSlug()
  const activeTimers: number[] = []

  // Clean up any timers on navigation
  window.addCleanup(() => {
    activeTimers.forEach((t) => clearInterval(t))
  })

  // =========================================================================
  // 1. IELTS WRITING WORKSPACE
  // =========================================================================
  const writingCards = document.querySelectorAll<HTMLElement>(".ielts-writing-card")
  writingCards.forEach((card) => {
    const taskId = card.dataset.task || "task-1"
    const targetWords = parseInt(card.dataset.target || "150", 10)
    const initialMinutes = parseInt(card.dataset.timer || "20", 10)

    const textKey = `ielts_write_${slug}_${taskId}`
    const timeKey = `ielts_time_${slug}_${taskId}`

    const textarea = card.querySelector<HTMLTextAreaElement>(".ielts-textarea")
    const wordCountEl = card.querySelector<HTMLElement>(".ielts-word-count")
    const progressPillEl = card.querySelector<HTMLElement>(".ielts-progress-pill")
    const saveIndicatorEl = card.querySelector<HTMLElement>(".ielts-save-text")
    const timerDisplayEl = card.querySelector<HTMLElement>(".ielts-timer-display")
    const btnStart = card.querySelector<HTMLButtonElement>(".ielts-btn-start")
    const btnPause = card.querySelector<HTMLButtonElement>(".ielts-btn-pause")
    const btnReset = card.querySelector<HTMLButtonElement>(".ielts-btn-reset")
    const btnCopy = card.querySelector<HTMLButtonElement>(".ielts-btn-copy")
    const btnDownload = card.querySelector<HTMLButtonElement>(".ielts-btn-download")
    const btnClear = card.querySelector<HTMLButtonElement>(".ielts-btn-clear")

    if (!textarea) return

    // Load saved text
    const savedText = localStorage.getItem(textKey)
    if (savedText && !textarea.value) {
      textarea.value = savedText
    }

    // Helper: Count words
    function updateWordStats() {
      const text = textarea?.value || ""
      const words = text.trim() ? (text.match(/\b[\w'-]+\b/g) || []).length : 0

      if (wordCountEl) {
        wordCountEl.textContent = `${words} từ`
      }

      if (progressPillEl) {
        if (words === 0) {
          progressPillEl.textContent = `Chưa nhập bài (Mục tiêu: ≥ ${targetWords})`
          progressPillEl.className = "ielts-progress-pill ielts-pill-neutral"
        } else if (words < targetWords) {
          progressPillEl.textContent = `⚠️ Còn thiếu ${targetWords - words} từ (${words}/${targetWords})`
          progressPillEl.className = "ielts-progress-pill ielts-pill-warn"
        } else {
          progressPillEl.textContent = `✅ Đạt yêu cầu (${words}/${targetWords} từ)`
          progressPillEl.className = "ielts-progress-pill ielts-pill-success"
        }
      }
    }

    updateWordStats()

    // Autosave on input (debounce)
    let saveTimeout: number | undefined
    const onInput = () => {
      updateWordStats()
      if (saveIndicatorEl) {
        saveIndicatorEl.textContent = "Đang lưu..."
      }
      clearTimeout(saveTimeout)
      saveTimeout = window.setTimeout(() => {
        localStorage.setItem(textKey, textarea.value)
        if (saveIndicatorEl) {
          const now = new Date()
          const timeStr = now.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
          saveIndicatorEl.textContent = `🟢 Đã lưu vào máy (${timeStr})`
        }
      }, 400)
    }

    textarea.addEventListener("input", onInput)
    window.addCleanup(() => textarea.removeEventListener("input", onInput))

    // Timer Logic
    let totalSeconds = initialMinutes * 60
    let remainingSeconds = totalSeconds
    let timerInterval: number | undefined
    let isRunning = false

    function formatTime(sec: number): string {
      const m = Math.floor(sec / 60)
      const s = sec % 60
      return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
    }

    function updateTimerDisplay() {
      if (timerDisplayEl) {
        timerDisplayEl.textContent = formatTime(remainingSeconds)
      }
    }

    updateTimerDisplay()

    function startTimer() {
      if (isRunning) return
      isRunning = true
      if (btnStart) btnStart.style.display = "none"
      if (btnPause) btnPause.style.display = "inline-flex"

      timerInterval = window.setInterval(() => {
        if (remainingSeconds > 0) {
          remainingSeconds--
          updateTimerDisplay()
          sessionStorage.setItem(timeKey, String(remainingSeconds))
        } else {
          clearInterval(timerInterval)
          isRunning = false
          if (btnStart) btnStart.style.display = "inline-flex"
          if (btnPause) btnPause.style.display = "none"
          if (timerDisplayEl) {
            timerDisplayEl.textContent = "00:00 (Hết giờ!)"
            timerDisplayEl.classList.add("ielts-timer-alert")
          }
        }
      }, 1000)
      activeTimers.push(timerInterval)
    }

    function pauseTimer() {
      if (!isRunning) return
      isRunning = false
      clearInterval(timerInterval)
      if (btnStart) btnStart.style.display = "inline-flex"
      if (btnPause) btnPause.style.display = "none"
    }

    function resetTimer() {
      pauseTimer()
      remainingSeconds = totalSeconds
      updateTimerDisplay()
      sessionStorage.removeItem(timeKey)
      if (timerDisplayEl) {
        timerDisplayEl.classList.remove("ielts-timer-alert")
      }
    }

    btnStart?.addEventListener("click", startTimer)
    btnPause?.addEventListener("click", pauseTimer)
    btnReset?.addEventListener("click", resetTimer)

    // Copy to AI
    btnCopy?.addEventListener("click", () => {
      const text = textarea.value.trim()
      if (!text) {
        alert("Khung bài làm đang trống! Hãy viết bài trước khi sao chép.")
        return
      }

      const words = (text.match(/\b[\w'-]+\b/g) || []).length
      const spentSec = totalSeconds - remainingSeconds
      const spentMin = Math.floor(spentSec / 60)
      const spentSecRemainder = spentSec % 60
      const spentStr = `${spentMin} phút ${spentSecRemainder} giây`

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
      ].join("\n")

      navigator.clipboard.writeText(promptPayload).then(() => {
        const origText = btnCopy.textContent
        btnCopy.textContent = "✅ Đã Sao Chép! Hãy dán vào chat"
        btnCopy.classList.add("ielts-btn-success")
        setTimeout(() => {
          btnCopy.textContent = origText
          btnCopy.classList.remove("ielts-btn-success")
        }, 3000)
      })
    })

    // Download .md file
    btnDownload?.addEventListener("click", () => {
      const text = textarea.value.trim()
      if (!text) {
        alert("Khung bài làm đang trống!")
        return
      }
      const words = (text.match(/\b[\w'-]+\b/g) || []).length
      const mdContent = `# Bài Làm IELTS Writing - ${taskId.toUpperCase()}\n\n- **Ngày làm:** ${new Date().toLocaleDateString("vi-VN")}\n- **Số từ:** ${words} từ\n\n---\n\n${text}\n`
      const blob = new Blob([mdContent], { type: "text/markdown;charset=utf-8" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `ielts-writing-${taskId}.md`
      a.click()
      URL.revokeObjectURL(url)
    })

    // Clear and reset
    btnClear?.addEventListener("click", () => {
      if (confirm("Bạn có chắc chắn muốn xóa bài làm này để làm lại từ đầu?")) {
        textarea.value = ""
        localStorage.removeItem(textKey)
        resetTimer()
        updateWordStats()
        if (saveIndicatorEl) {
          saveIndicatorEl.textContent = "Đã làm mới khung bài làm."
        }
      }
    })
  })

  // =========================================================================
  // 2. IELTS INTERACTIVE ANSWER SHEET (Reading & Listening)
  // =========================================================================
  const sheetCards = document.querySelectorAll<HTMLElement>(".ielts-sheet-card")
  sheetCards.forEach((card) => {
    const sheetId = card.dataset.sheetId || "sheet-1"
    const startQ = parseInt(card.dataset.startQ || "1", 10)
    const endQ = parseInt(card.dataset.endQ || "40", 10)
    const storageKey = `ielts_sheet_${slug}_${sheetId}`

    const gridContainer = card.querySelector<HTMLElement>(".ielts-grid-answers")
    const progressEl = card.querySelector<HTMLElement>(".ielts-sheet-progress")
    const saveIndicatorEl = card.querySelector<HTMLElement>(".ielts-sheet-save-text")
    const btnCopy = card.querySelector<HTMLButtonElement>(".ielts-btn-copy-shorthand")
    const btnClear = card.querySelector<HTMLButtonElement>(".ielts-btn-clear-sheet")

    if (!gridContainer) return

    // Render cells if empty
    if (!gridContainer.children.length) {
      const fragment = document.createDocumentFragment()
      for (let q = startQ; q <= endQ; q++) {
        const cell = document.createElement("div")
        cell.className = "ielts-q-cell"
        cell.innerHTML = `
          <span class="ielts-q-num">${q}</span>
          <input type="text" class="ielts-q-input" data-q="${q}" placeholder="..." autocomplete="off" spellcheck="false" />
        `
        fragment.appendChild(cell)
      }
      gridContainer.appendChild(fragment)
    }

    const inputs = card.querySelectorAll<HTMLInputElement>(".ielts-q-input")

    // Load saved answers
    let answers: Record<string, string> = {}
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw) answers = JSON.parse(raw)
    } catch (e) {}

    inputs.forEach((input) => {
      const q = input.dataset.q!
      if (answers[q]) {
        input.value = answers[q]
      }
    })

    function updateProgress() {
      let filled = 0
      inputs.forEach((i) => {
        if (i.value.trim()) filled++
      })
      const total = endQ - startQ + 1
      if (progressEl) {
        progressEl.textContent = `${filled} / ${total} câu đã điền`
      }
    }

    updateProgress()

    // Handle input change & enter navigation
    inputs.forEach((input, idx) => {
      input.addEventListener("input", () => {
        const q = input.dataset.q!
        answers[q] = input.value.trim()
        localStorage.setItem(storageKey, JSON.stringify(answers))
        updateProgress()
        if (saveIndicatorEl) {
          saveIndicatorEl.textContent = "🟢 Đã lưu vào máy"
        }
      })

      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === "Tab") {
          e.preventDefault()
          const next = inputs[idx + 1]
          if (next) {
            next.focus()
            next.select()
          }
        }
      })
    })

    // Copy Shorthand for AI
    btnCopy?.addEventListener("click", () => {
      const lines: string[] = []
      let filledCount = 0

      for (let q = startQ; q <= endQ; q++) {
        const val = answers[String(q)] || ""
        if (val) {
          lines.push(`${q} ${val}`)
          filledCount++
        }
      }

      if (filledCount === 0) {
        alert("Bảng đáp án đang trống! Hãy điền câu trả lời trước khi sao chép.")
        return
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
      ].join("\n")

      navigator.clipboard.writeText(promptPayload).then(() => {
        const origText = btnCopy.textContent
        btnCopy.textContent = "✅ Đã Sao Chép Shorthand!"
        btnCopy.classList.add("ielts-btn-success")
        setTimeout(() => {
          btnCopy.textContent = origText
          btnCopy.classList.remove("ielts-btn-success")
        }, 3000)
      })
    })

    // Clear answers
    btnClear?.addEventListener("click", () => {
      if (confirm("Bạn có chắc chắn muốn xóa toàn bộ câu trả lời trong bảng này?")) {
        inputs.forEach((i) => (i.value = ""))
        answers = {}
        localStorage.removeItem(storageKey)
        updateProgress()
        if (saveIndicatorEl) {
          saveIndicatorEl.textContent = "Đã xóa sạch đáp án."
        }
      }
    })
  })
})
