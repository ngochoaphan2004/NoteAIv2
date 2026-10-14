import React, { useState, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, FlashcardItem } from "../services/api";
import {
  BookOpen,
  Calendar,
  ExternalLink,
  RotateCw,
  ArrowRight,
  Compass,
  Home,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

const QUARTZ_BASE_URL = "http://localhost:8088";

interface DailySessionProps {
  onNavigateToFlashcards: () => void;
}

export const DailySession: React.FC<DailySessionProps> = ({
  onNavigateToFlashcards,
}) => {
  // Đường dẫn mặc định trỏ thẳng vào kế hoạch Tuần 1 (đang diễn ra từ 14/10)
  const [currentUrl, setCurrentUrl] = useState(
    `${QUARTZ_BASE_URL}/plans/week-01/`,
  );
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Lấy số lượng thẻ cần ôn hôm nay từ FastAPI backend
  const { data: dueCards = [] } = useQuery<FlashcardItem[]>({
    queryKey: ["flashcards", "due"],
    queryFn: () => api.getDueCards(50),
    staleTime: 1000 * 60, // 1 phút
  });

  const dueCount = dueCards.length;

  const quickNavLinks = [
    {
      label: "Tuần 1 (14/10 – 20/10)",
      path: "/plans/week-01/",
      icon: <Calendar className="w-3.5 h-3.5 text-apple-blue" />,
      badge: "Hiện tại",
    },
    {
      label: "Tất cả kế hoạch",
      path: "/plans/",
      icon: <Compass className="w-3.5 h-3.5" />,
    },
    {
      label: "Lộ trình 5.0 → 7.5",
      path: "/roadmap-5.0-to-7.5",
      icon: <Sparkles className="w-3.5 h-3.5 text-purple-500" />,
    },
    {
      label: "Trang chủ Vườn",
      path: "/",
      icon: <Home className="w-3.5 h-3.5" />,
    },
  ];

  const handleNavigate = (path: string) => {
    const fullUrl = `${QUARTZ_BASE_URL}${path}`;
    setCurrentUrl(fullUrl);
    if (iframeRef.current) {
      iframeRef.current.src = fullUrl;
    }
  };

  const handleRefresh = () => {
    if (iframeRef.current) {
      iframeRef.current.src = currentUrl;
    }
  };

  return (
    <div className="flex flex-col gap-3 h-[calc(100vh-8.5rem)]">
      {/* Action Header: Thanh điều hướng Kế hoạch & Chuyển bước Flashcard */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white dark:bg-[#1c1c1e] p-3.5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm flex-shrink-0">
        {/* Quick Links Chọn Kế Hoạch Trong Vườn Tri Thức */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          <span className="text-xs font-bold text-apple-subtextLight dark:text-apple-subtextDark mr-1 flex items-center gap-1">
            <BookOpen className="w-4 h-4 text-apple-blue" />
            Kế Hoạch:
          </span>

          {quickNavLinks.map((item) => {
            const isActive = currentUrl === `${QUARTZ_BASE_URL}${item.path}`;
            return (
              <button
                key={item.path}
                onClick={() => handleNavigate(item.path)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 whitespace-nowrap ${
                  isActive
                    ? "bg-apple-blue text-white shadow-sm"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                      isActive
                        ? "bg-white/20 text-white"
                        : "bg-blue-100 dark:bg-blue-900/50 text-apple-blue"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Nút Hành Động Trọng Tâm: Chuyển Sang Hoàn Thành Flashcard Sau Khi Học Xong Plan */}
        <div className="flex items-center gap-2 justify-end flex-shrink-0">
          <button
            onClick={handleRefresh}
            title="Tải lại nội dung trang"
            className="p-2 text-gray-500 hover:text-apple-blue hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition border border-gray-200 dark:border-gray-700"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          <a
            href={currentUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Mở tab mới trong trình duyệt"
            className="p-2 text-gray-500 hover:text-apple-blue hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition border border-gray-200 dark:border-gray-700"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <button
            onClick={onNavigateToFlashcards}
            className="group px-4 py-2 bg-gradient-to-r from-apple-blue to-indigo-600 hover:from-apple-blueHover hover:to-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4 text-white" />
            <span>Đã làm xong bài? Tới Ôn Thẻ Nhớ</span>
            {dueCount > 0 ? (
              <span className="bg-white text-apple-blue text-[10px] px-1.5 py-0.5 rounded-full font-extrabold shadow-sm">
                {dueCount} thẻ
              </span>
            ) : (
              <span className="bg-white/20 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                Sẵn sàng
              </span>
            )}
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>

      {/* Main Content Area: Toàn bộ không gian dành cho Quartz Digital Garden */}
      <div className="flex-1 w-full bg-white dark:bg-[#1c1c1e] rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm flex flex-col">
        <iframe
          ref={iframeRef}
          src={currentUrl}
          title="Kế Hoạch Học Tập - Quartz Digital Garden"
          className="w-full h-full border-0 flex-1"
          allow="clipboard-write; clipboard-read"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
        />
      </div>
    </div>
  );
};

export default DailySession;
