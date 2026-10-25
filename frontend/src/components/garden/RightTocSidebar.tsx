import React, { useState, useEffect } from "react";
import { AlignLeft, ChevronRight, X } from "lucide-react";

export interface TocHeading {
  level: number;
  text: string;
  id: string;
}

interface RightTocSidebarProps {
  headings?: TocHeading[];
  isOpen: boolean;
  onToggle: () => void;
}

export const RightTocSidebar: React.FC<RightTocSidebarProps> = ({
  headings = [],
  isOpen,
  onToggle,
}) => {
  const [activeId, setActiveId] = useState<string>("");

  // Lắng nghe scroll để tự động phát hiện mục đang đọc (Scroll Spy)
  useEffect(() => {
    if (!headings || headings.length === 0) return;

    const handleScroll = () => {
      const scrollPosition = window.scrollY + 140;
      let currentActive = "";

      for (const heading of headings) {
        const el = document.getElementById(heading.id);
        if (el) {
          const top = el.getBoundingClientRect().top + window.scrollY;
          if (top <= scrollPosition) {
            currentActive = heading.id;
          }
        }
      }

      if (currentActive) {
        setActiveId(currentActive);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, [headings]);

  const handleHeadingClick = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveId(id);
      window.history.replaceState(null, "", `#${id}`);
    }
  };

  if (!isOpen) return null;

  // Lọc bỏ heading cấp 1 nếu trùng lặp hoàn toàn
  const displayHeadings = headings.filter((h) => h.level >= 1 && h.level <= 4);

  return (
    <aside className="w-56 xl:w-64 flex-shrink-0 border-l border-gray-200 dark:border-gray-800 p-4 sticky top-4 max-h-[calc(100vh-120px)] overflow-y-auto no-scrollbar hidden lg:flex flex-col select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-1.5 text-xs font-bold text-gray-800 dark:text-gray-200 tracking-wide uppercase">
          <AlignLeft className="w-3.5 h-3.5 text-apple-blue" />
          <span>Mục Lục Trang</span>
        </div>
        <button
          type="button"
          onClick={onToggle}
          title="Thu gọn mục lục"
          className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Danh sách các đề mục */}
      {displayHeadings.length === 0 ? (
        <div className="py-8 text-center text-xs text-gray-400 dark:text-gray-500">
          Tài liệu này không có mục lục
        </div>
      ) : (
        <nav className="space-y-1 text-xs">
          {displayHeadings.map((h, idx) => {
            const isActive = activeId === h.id;
            const indentClass =
              h.level === 1
                ? "pl-1 font-semibold"
                : h.level === 2
                ? "pl-3 text-[12px]"
                : h.level === 3
                ? "pl-5 text-[11.5px]"
                : "pl-7 text-[11px]";

            return (
              <a
                key={`${h.id}-${idx}`}
                href={`#${h.id}`}
                onClick={(e) => handleHeadingClick(e, h.id)}
                title={h.text}
                className={`group flex items-start gap-1.5 py-1 px-1.5 rounded-md transition leading-snug truncate ${indentClass} ${
                  isActive
                    ? "text-apple-blue font-bold bg-blue-50/70 dark:bg-blue-950/30"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100/70 dark:hover:bg-gray-800/50"
                }`}
              >
                <ChevronRight
                  className={`w-3 h-3 flex-shrink-0 mt-0.5 transition ${
                    isActive
                      ? "text-apple-blue rotate-90"
                      : "text-transparent group-hover:text-gray-300 dark:group-hover:text-gray-600"
                  }`}
                />
                <span className="truncate">{h.text}</span>
              </a>
            );
          })}
        </nav>
      )}
    </aside>
  );
};
