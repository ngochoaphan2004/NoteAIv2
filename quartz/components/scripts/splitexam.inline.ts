let isSplitExamActive = false;
let currentActiveDetailsIndex = 0;
let currentZoom = 95;

function getExamDetailsList(): HTMLDetailsElement[] {
  const allDetails = Array.from(
    document.querySelectorAll<HTMLDetailsElement>("article details, .center details, details"),
  );
  // Filter for details that contain images or have class ielts-exam-prompt
  return allDetails.filter((d) => {
    return d.classList.contains("ielts-exam-prompt") || d.querySelector("img") !== null;
  });
}

function updateZoom(newZoom: number) {
  currentZoom = Math.min(160, Math.max(60, newZoom));
  const panel = document.getElementById("split-exam-panel");
  if (panel) {
    panel.style.setProperty("--split-zoom", `${currentZoom}%`);
    const zoomLabel = panel.querySelector(".split-zoom-label");
    if (zoomLabel) zoomLabel.textContent = `${currentZoom}%`;
  }
}

function setSplitRatio(leftPct: number) {
  const rightPct = 100 - leftPct;
  document.documentElement.style.setProperty("--split-left-width", `${leftPct}%`);
  document.documentElement.style.setProperty("--split-right-width", `${rightPct}%`);

  const centerEl = document.querySelector<HTMLElement>(".center");
  if (centerEl && isSplitExamActive) {
    centerEl.style.width = `${leftPct}%`;
    centerEl.style.maxWidth = `${leftPct}%`;
  }

  const panel = document.getElementById("split-exam-panel");
  if (panel) {
    panel.style.width = `${rightPct}%`;
    const ratioBtns = panel.querySelectorAll<HTMLButtonElement>(".split-ratio-group .split-tool-btn");
    ratioBtns.forEach((btn) => {
      const r = parseInt(btn.dataset.ratio || "50", 10);
      btn.classList.toggle("active", r === leftPct);
    });
  }
}

function showToast(message: string) {
  const existing = document.querySelector(".split-toast-notice");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "split-toast-notice";
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(30, 30, 30, 0.92);
    color: #ffffff;
    padding: 8px 18px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 500;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    z-index: 99999;
    backdrop-filter: blur(10px);
    transition: opacity 0.25s ease;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 250);
  }, 2500);
}

function exitSplitExamMode() {
  if (!isSplitExamActive) return;
  isSplitExamActive = false;
  document.documentElement.setAttribute("split-mode", "off");

  // Restore center column width
  const centerEl = document.querySelector<HTMLElement>(".center");
  if (centerEl) {
    centerEl.style.width = "";
    centerEl.style.maxWidth = "";
    centerEl.style.height = "";
    centerEl.style.overflowY = "";
  }

  // Restore hidden original details
  const allDetails = document.querySelectorAll<HTMLDetailsElement>("details.split-projected");
  allDetails.forEach((d) => d.classList.remove("split-projected"));

  // Remove top notice in left column
  const notice = document.querySelector(".split-left-notice");
  if (notice) notice.remove();

  // Hide right panel
  const panel = document.getElementById("split-exam-panel");
  if (panel) {
    panel.style.display = "none";
    const imagesContent = panel.querySelector(".split-images-content");
    if (imagesContent) imagesContent.innerHTML = "";
  }
}

function activateSplitExamMode(targetIndex: number = 0) {
  const detailsList = getExamDetailsList();
  if (detailsList.length === 0) {
    showToast("⚠️ Ghi chú này không chứa tài liệu đề thi (ảnh) để chia 2 cột.");
    return;
  }

  isSplitExamActive = true;
  currentActiveDetailsIndex = Math.min(Math.max(0, targetIndex), detailsList.length - 1);
  document.documentElement.setAttribute("split-mode", "on");

  // Mount directly to document.body for guaranteed top-level fixed placement
  let panel = document.getElementById("split-exam-panel");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "split-exam-panel";
    document.body.appendChild(panel);
  }

  panel.style.display = "flex";

  // Set default ratio & zoom
  setSplitRatio(50);
  updateZoom(currentZoom);

  // Apply explicit dimensions to .center
  const centerEl = document.querySelector<HTMLElement>(".center");
  if (centerEl) {
    centerEl.style.width = "50%";
    centerEl.style.maxWidth = "50%";
    centerEl.style.height = "100vh";
    centerEl.style.overflowY = "auto";
  }

  // Render Panel Structure
  panel.innerHTML = `
    <div class="split-panel-header">
      <div class="split-header-left">
        <span class="split-panel-badge">📖 ĐỀ BÀI</span>
        <div class="split-tabs-wrap"></div>
      </div>
      <div class="split-header-right">
        <div class="split-btn-group split-ratio-group">
          <button type="button" class="split-tool-btn active" data-ratio="50" title="Chia đôi 50:50">50:50</button>
          <button type="button" class="split-tool-btn" data-ratio="40" title="Bài làm 40% - Đề thi 60%">40:60</button>
          <button type="button" class="split-tool-btn" data-ratio="60" title="Bài làm 60% - Đề thi 40%">60:40</button>
        </div>
        <div class="split-btn-group split-zoom-group">
          <button type="button" class="split-tool-btn split-zoom-out" title="Thu nhỏ ảnh">➖</button>
          <span class="split-zoom-label">${currentZoom}%</span>
          <button type="button" class="split-tool-btn split-zoom-in" title="Phóng to ảnh">➕</button>
        </div>
        <button type="button" class="split-exit-btn" title="Thoát chế độ 2 cột (Esc)">
          <span>✖</span> Thoát
        </button>
      </div>
    </div>
    <div class="split-panel-body">
      <div class="split-images-content"></div>
    </div>
  `;

  // Attach Exit & Tool listeners
  const btnExit = panel.querySelector<HTMLButtonElement>(".split-exit-btn");
  btnExit?.addEventListener("click", exitSplitExamMode);

  const ratioBtns = panel.querySelectorAll<HTMLButtonElement>(".split-ratio-group .split-tool-btn");
  ratioBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const r = parseInt(btn.dataset.ratio || "50", 10);
      setSplitRatio(r);
    });
  });

  const btnZoomIn = panel.querySelector<HTMLButtonElement>(".split-zoom-in");
  const btnZoomOut = panel.querySelector<HTMLButtonElement>(".split-zoom-out");
  btnZoomIn?.addEventListener("click", () => updateZoom(currentZoom + 10));
  btnZoomOut?.addEventListener("click", () => updateZoom(currentZoom - 10));

  // Render Tabs & Images
  const tabsWrap = panel.querySelector<HTMLElement>(".split-tabs-wrap");
  const imagesContent = panel.querySelector<HTMLElement>(".split-images-content");

  function renderActiveDetails() {
    if (!tabsWrap || !imagesContent) return;

    tabsWrap.innerHTML = "";
    detailsList.forEach((detailEl, idx) => {
      const summaryText =
        detailEl.querySelector("summary")?.textContent?.replace(/\[.*?\]/g, "").trim() ||
        `Phần ${idx + 1}`;

      // Shorten label for tab
      let shortLabel = summaryText
        .replace(/^\d+[\.\)]\s*/, "")
        .replace(/^(📄|📜|🎧|📖)\s*/, "")
        .replace(/Cambridge\s*\d+\s*-\s*/i, "")
        .trim();
      if (shortLabel.length > 25) shortLabel = shortLabel.substring(0, 24) + "…";

      const tabBtn = document.createElement("button");
      tabBtn.type = "button";
      tabBtn.className = `split-tab-btn ${idx === currentActiveDetailsIndex ? "active" : ""}`;
      tabBtn.textContent = shortLabel;
      tabBtn.title = summaryText;
      tabBtn.addEventListener("click", () => {
        currentActiveDetailsIndex = idx;
        renderActiveDetails();
      });
      tabsWrap.appendChild(tabBtn);
    });

    // Hide active detail in center column & display clone in right panel
    detailsList.forEach((detailEl, idx) => {
      detailEl.classList.toggle("split-projected", idx === currentActiveDetailsIndex);
    });

    const activeDetail = detailsList[currentActiveDetailsIndex];
    imagesContent.innerHTML = "";

    if (activeDetail) {
      // Clone all children except <summary>
      Array.from(activeDetail.children).forEach((child) => {
        if (child.tagName.toLowerCase() !== "summary") {
          const clone = child.cloneNode(true) as HTMLElement;
          // Ensure image p tags have zero margin class
          if (clone.tagName.toLowerCase() === "p" && clone.querySelector("img")) {
            clone.classList.add("ielts-exam-img-p");
          }
          imagesContent.appendChild(clone);
        }
      });
    }

    // Scroll right panel to top
    const panelBody = panel?.querySelector(".split-panel-body");
    if (panelBody) panelBody.scrollTop = 0;
  }

  renderActiveDetails();

  // Add notification pill in left column
  if (centerEl && !centerEl.querySelector(".split-left-notice")) {
    const notice = document.createElement("div");
    notice.className = "split-left-notice";
    notice.innerHTML = `
      <span>🖥️ <strong>Chế độ thi 2 cột:</strong> Đề bài đang hiển thị ở cột bên phải. Làm bài & ghi chú ở cột này.</span>
      <button type="button" class="split-tool-btn split-exit-notice-btn" style="color:var(--secondary); font-weight:600;">Thoát (Esc) ✖</button>
    `;
    notice.querySelector(".split-exit-notice-btn")?.addEventListener("click", exitSplitExamMode);
    centerEl.insertBefore(notice, centerEl.firstChild);
  }
}

// Global Event Listeners & Lifecycle Setup
document.addEventListener("nav", () => {
  // Always reset split mode on navigation
  exitSplitExamMode();

  const detailsList = getExamDetailsList();

  // 1. Normalize image paragraphs in details
  document.querySelectorAll<HTMLElement>("details p").forEach((p) => {
    if (p.querySelector("img")) {
      p.classList.add("ielts-exam-img-p");
    }
  });

  // 2. Inject quick trigger button into summary of exam details
  detailsList.forEach((detailEl, idx) => {
    const summary = detailEl.querySelector("summary");
    if (summary && !summary.querySelector(".ielts-details-split-btn")) {
      const splitBtn = document.createElement("button");
      splitBtn.type = "button";
      splitBtn.className = "ielts-details-split-btn";
      splitBtn.title = "Mở đề bài ở chế độ 2 cột độc lập";
      splitBtn.innerHTML = `🖥️ Xem 2 Cột`;
      splitBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        activateSplitExamMode(idx);
      });
      summary.appendChild(splitBtn);
    }
  });

  // 3. Connect sidebar/header icon buttons
  const splitModeButtons = document.querySelectorAll<HTMLButtonElement>(".splitexammode");
  splitModeButtons.forEach((btn) => {
    const onToggle = () => {
      if (isSplitExamActive) {
        exitSplitExamMode();
      } else {
        activateSplitExamMode(0);
      }
    };
    btn.addEventListener("click", onToggle);
    window.addCleanup(() => btn.removeEventListener("click", onToggle));
  });

  // 4. Keyboard Shortcuts
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape" && isSplitExamActive) {
      exitSplitExamMode();
    } else if (e.altKey && (e.key === "s" || e.key === "S")) {
      e.preventDefault();
      if (isSplitExamActive) {
        exitSplitExamMode();
      } else {
        activateSplitExamMode(0);
      }
    }
  };

  window.addEventListener("keydown", onKeyDown);
  window.addCleanup(() => window.removeEventListener("keydown", onKeyDown));

  // 5. Listen for custom event from interactive cards
  const onCustomOpen = (e: Event) => {
    const detail = (e as CustomEvent).detail;
    const targetIdx = detail && typeof detail.index === "number" ? detail.index : 0;
    activateSplitExamMode(targetIdx);
  };

  document.addEventListener("splitscreen-open", onCustomOpen);
  window.addCleanup(() => document.removeEventListener("splitscreen-open", onCustomOpen));

  // 6. Listen for postMessage from parent React SPA
  const onMessage = (e: MessageEvent) => {
    if (e.data?.type === "TOGGLE_SPLIT_MODE") {
      if (isSplitExamActive) {
        exitSplitExamMode();
      } else {
        activateSplitExamMode(0);
      }
    }
  };
  window.addEventListener("message", onMessage);
  window.addCleanup(() => window.removeEventListener("message", onMessage));

  // 7. Notify parent React SPA on scroll so top bars can auto-hide
  let lastScrollY = window.scrollY;
  const onScroll = () => {
    const curY = window.scrollY;
    const isScrollingDown = curY > lastScrollY && curY > 30;
    lastScrollY = curY;
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(
        {
          type: "IFRAME_SCROLL_STATE",
          isScrollingDown,
          scrollY: curY,
        },
        "*",
      );
    }
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addCleanup(() => window.removeEventListener("scroll", onScroll));
});
