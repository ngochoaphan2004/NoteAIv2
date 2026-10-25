import { useState, useEffect, useCallback } from "react";

export type TabType = "session" | "flashcards" | "rag" | "stats" | "config";

export interface AppRoute {
  tab: TabType;
  notePath?: string;
  pathname: string;
}

const TAB_ROUTES: Record<string, TabType> = {
  flashcards: "flashcards",
  rag: "rag",
  stats: "stats",
  config: "config",
  session: "session",
};

/**
 * Chuyển đổi chuỗi tiếng Việt có dấu thành slug không dấu chuẩn ASCII cho anchor ID và URL.
 * Ví dụ: "📝 Bảng Ghi Nhận Bài Làm Của Bạn" -> "bang-ghi-nhan-bai-lam-cua-ban"
 */
export function slugifyText(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Chuyển đổi đường dẫn file Markdown (ví dụ: plans/week-01/test-1-listening-p1-p2.md)
 * thành URL slug sạch chuẩn Web (ví dụ: /plans/week-01/test-1-listening-p1-p2).
 */
export function pathToSlug(rawPath: string): string {
  let clean = rawPath.replace(/\\/g, "/").replace(/^\/+|\/+$/g, "");
  if (clean.startsWith("content/")) {
    clean = clean.slice("content/".length);
  }
  if (clean.endsWith(".md")) {
    clean = clean.slice(0, -3);
  }
  if (clean.endsWith("/index")) {
    clean = clean.slice(0, -6);
  } else if (clean === "index") {
    clean = "";
  }
  return clean ? `/${clean}` : "/";
}

/**
 * Phân giải pathname trên thanh địa chỉ URL thành route trạng thái của ứng dụng.
 */
export function parseRoute(pathname: string): AppRoute {
  const clean = pathname.replace(/^\/+|\/+$/g, "");

  // 1. Trang chủ hoặc /session
  if (!clean || clean === "session") {
    const saved = typeof window !== "undefined" ? localStorage.getItem("noteai_last_note_path") : null;
    return {
      tab: "session",
      notePath: saved || "plans/week-01/index.md",
      pathname: !clean ? "/" : `/${clean}`,
    };
  }

  // 2. Các tab chính cố định (/flashcards, /rag, /stats, /config)
  if (TAB_ROUTES[clean]) {
    return {
      tab: TAB_ROUTES[clean],
      pathname: `/${clean}`,
    };
  }

  // 3. Đường dẫn ghi chú trong Digital Garden (ví dụ: /plans/week-01/test-1-listening-p1-p2)
  let noteRel = clean;
  if (noteRel.startsWith("note/")) {
    noteRel = noteRel.slice("note/".length);
  }

  // Chuẩn hóa đuôi .md nếu chưa có
  if (!noteRel.endsWith(".md") && !noteRel.includes("#")) {
    // Nếu là thư mục như plans/week-01 không có bài test cụ thể -> mở index.md
    if (
      noteRel.startsWith("plans/week-") &&
      !noteRel.includes("test-") &&
      !noteRel.includes("vocab-") &&
      !noteRel.includes("review-")
    ) {
      noteRel = `${noteRel}/index.md`;
    } else {
      noteRel = `${noteRel}.md`;
    }
  }

  return {
    tab: "session",
    notePath: noteRel,
    pathname: `/${clean}`,
  };
}

/**
 * Điều hướng URL của trình duyệt không làm reload trang, kích hoạt sự kiện cho React cập nhật.
 */
export function navigateTo(target: string, replace = false): void {
  let targetUrl = target;

  // Nếu target là tên tab
  if (TAB_ROUTES[target]) {
    targetUrl = target === "session" ? "/" : `/${target}`;
  } else if (!target.startsWith("/")) {
    targetUrl = pathToSlug(target);
  }

  if (window.location.pathname !== targetUrl) {
    if (replace) {
      window.history.replaceState(null, "", targetUrl);
    } else {
      window.history.pushState(null, "", targetUrl);
    }
    window.dispatchEvent(new CustomEvent("noteai:navigate", { detail: { url: targetUrl } }));
  }
}

/**
 * React Hook đồng bộ 2 chiều giữa URL trình duyệt và trạng thái hiển thị của ứng dụng.
 */
export function useRouter() {
  const [route, setRoute] = useState<AppRoute>(() =>
    typeof window !== "undefined"
      ? parseRoute(window.location.pathname)
      : { tab: "session", notePath: "plans/week-01/index.md", pathname: "/" }
  );

  useEffect(() => {
    const handleUrlChange = () => {
      setRoute(parseRoute(window.location.pathname));
    };

    window.addEventListener("popstate", handleUrlChange);
    window.addEventListener("noteai:navigate", handleUrlChange);

    return () => {
      window.removeEventListener("popstate", handleUrlChange);
      window.removeEventListener("noteai:navigate", handleUrlChange);
    };
  }, []);

  const navigate = useCallback((target: string, replace = false) => {
    navigateTo(target, replace);
  }, []);

  return {
    route,
    navigate,
    tab: route.tab,
    notePath: route.notePath,
  };
}
