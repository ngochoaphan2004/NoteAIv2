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
  Zap,
  CheckCheck,
  Columns,
  Headphones,
  FileText,
  Edit3,
} from "lucide-react";

const QUARTZ_BASE_URL =
  typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:8088`
    : "http://localhost:8088";

interface DailySessionProps {
  onNavigateToFlashcards: () => void;
}

export const DailySession: React.FC<DailySessionProps> = ({
  onNavigateToFlashcards,
}) => {
  const [currentUrl, setCurrentUrl] = useState(
    `${QUARTZ_BASE_URL}/plans/week-01/`,
  );
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isScrolledDown, setIsScrolledDown] = useState(false);

  // Lấy thông tin nhiệm vụ ngày hôm nay từ AI Plan Service
  const { data: todayPlan, refetch: refetchTodayPlan } = useQuery({
    queryKey: ["plans", "today"],
    queryFn: () => api.getTodayPlan(),
    staleTime: 1000 * 60 * 2, // 2 phút
  });

  // Lấy số lượng thẻ cần ôn hôm nay từ FastAPI backend
  const { data: dueCards = [] } = useQuery<FlashcardItem[]>({
    queryKey: ["flashcards", "due"],
    queryFn: () => api.getDueCards(50),
    staleTime: 1000 * 60, // 1 phút
  });

  // Lắng nghe sự kiện từ Quartz iframe (Nộp bài thi & Cuộn trang)
  React.useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === "IELTS_TEST_SUBMITTED") {
        const { filledCount, skill } = event.data.payload || {};
        const skillName = skill === "reading" ? "Reading" : "Listening";
        setToastMessage(
          `🤖 AI đã tiếp nhận thành công bài làm ${skillName} (${filledCount} câu)! Kế hoạch học tập tuần đã tự động chuyển trạng thái hoàn thành.`
        );
        refetchTodayPlan();
        setTimeout(() => {
          setToastMessage(null);
        }, 6000);
      } else if (event.data?.type === "IFRAME_SCROLL_STATE") {
        setIsScrolledDown(Boolean(event.data.isScrollingDown));
      }
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [refetchTodayPlan]);

  // Lắng nghe cuộn cửa sổ chính (window scroll)
  React.useEffect(() => {
    let lastY = window.scrollY;
    const onScroll = () => {
      const curY = window.scrollY;
      if (curY > 50 && curY > lastY) {
        setIsScrolledDown(true);
      } else if (curY < lastY || curY <= 15) {
        setIsScrolledDown(false);
      }
      lastY = curY;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const dueCount = dueCards.length;

  const quickNavLinks = [
    {
      label: "Kế Hoạch Tuần 1",
      path: "/plans/week-01/",
      icon: <Calendar className="w-3.5 h-3.5 text-apple-blue" />,
      badge: "Hiện tại",
    },
    {
      label: "Lộ trình 5.0 → 7.5",
      path: "/roadmap-5.0-to-7.5",
      icon: <Sparkles className="w-3.5 h-3.5 text-purple-500" />,
    },
  ];

  const handleToggleSplitMode = () => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ type: "TOGGLE_SPLIT_MODE" }, "*");
    }
  };

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

  const handleAutoSync = async () => {
    try {
      setIsSyncing(true);
      const res = await api.syncPlans();
      await refetchTodayPlan();
      handleRefresh();
      setToastMessage(
        `⚡ AI đã tự động đồng bộ kế hoạch theo ngày ${res.today} và tiến độ cá nhân!`
      );
      setTimeout(() => setToastMessage(null), 5000);
    } catch (err: any) {
      alert(`Lỗi đồng bộ kế hoạch: ${err.message || err}`);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 pb-6">
      {/* Nút Phục Hồi Thanh Công Cụ Nhỏ Gọn Khi Đang Cuộn Bài */}
      {isScrolledDown && (
        <button
          onClick={() => setIsScrolledDown(false)}
          className="fixed top-2.5 left-1/2 -translate-x-1/2 z-40 bg-white/95 dark:bg-[#1c1c1e]/95 backdrop-blur-md px-3.5 py-1 rounded-full border border-gray-200 dark:border-gray-700 shadow-md text-[11px] font-semibold text-gray-700 dark:text-gray-300 hover:text-apple-blue transition flex items-center gap-1.5"
        >
          <span>▲ Hiện Lại Thanh Kế Hoạch</span>
        </button>
      )}

      {/* 2 Thanh bar: Tự động trượt lên và biến mất khi cuộn bài để tối đa không gian */}
      <div
        className={`flex flex-col gap-3 transition-all duration-300 ease-in-out origin-top ${
          isScrolledDown
            ? "max-h-0 opacity-0 overflow-hidden pointer-events-none -my-2 scale-98"
            : "max-h-[600px] opacity-100 overflow-visible scale-100"
        }`}
      >
        {/* Banner AI Tự Động Định Hướng Nhiệm Vụ Hôm Nay */}
        {todayPlan && (
          <div className="bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-purple-500/10 border border-blue-500/20 px-4 py-3 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm transition">
            <div className="flex items-start gap-3">
              <span className="p-2 bg-apple-blue text-white rounded-xl shadow-sm mt-0.5 flex-shrink-0">
                <Zap className="w-4 h-4" />
              </span>
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-bold text-apple-blue uppercase tracking-wider">
                    Nhiệm Vụ {todayPlan.today}:
                  </span>
                  <span className="text-xs font-bold text-gray-900 dark:text-gray-100">
                    {todayPlan.skill}
                  </span>
                  {todayPlan.duration && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full border border-blue-200 dark:border-blue-800">
                      ⏱️ {todayPlan.duration}
                    </span>
                  )}
                </div>

                {todayPlan.steps && todayPlan.steps.length > 0 ? (
                  <div className="flex flex-col sm:flex-row sm:flex-wrap items-start sm:items-center gap-x-3 gap-y-1 text-[11px] text-gray-600 dark:text-gray-300">
                    {todayPlan.steps.map((step, idx) => (
                      <div key={idx} className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-apple-blue flex-shrink-0" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-gray-500 dark:text-gray-400">
                    {todayPlan.focus.replace(/<[^>]+>/g, " ").replace(/[*_`]/g, "")}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0 self-end md:self-auto">
              {todayPlan.is_done ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                  <CheckCheck className="w-3.5 h-3.5" />
                  Đã hoàn thành hôm nay
                </span>
              ) : (
                todayPlan.link && (
                  <button
                    onClick={() => {
                      const targetPath = todayPlan.link.startsWith("/")
                        ? todayPlan.link
                        : `/${todayPlan.link}`;
                      handleNavigate(targetPath.replace(/\/+$/, ""));
                    }}
                    className="px-3 py-1 bg-apple-blue hover:bg-apple-blueHover text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center gap-1"
                  >
                    <span>Vào bài học ngay</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                )
              )}

              <button
                onClick={handleAutoSync}
                disabled={isSyncing}
                title="Kích hoạt AI tự động đối soát tiến độ và ngày tháng"
                className="px-2.5 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:text-apple-blue text-xs font-medium rounded-lg border border-gray-200 dark:border-gray-700 transition flex items-center gap-1"
              >
                <RotateCw className={`w-3 h-3 ${isSyncing ? "animate-spin text-apple-blue" : ""}`} />
                <span>{isSyncing ? "Đang đồng bộ..." : "AI Tự Đồng Bộ"}</span>
              </button>
            </div>
          </div>
        )}

        {/* Action Header: Thanh điều hướng Kế hoạch chính (Chỉ giữ mục trọng tâm tránh cấn thông tin) */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white dark:bg-[#1c1c1e] p-3 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm transition">
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

          {/* Nút Tải lại, Mở Tab mới, Chế độ 2 Cột và Flashcard */}
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

            {/* Nút Kích Hoạt Nhanh Chế Độ Thi 2 Cột */}
            <button
              onClick={handleToggleSplitMode}
              title="Bật/Tắt chế độ thi chia 2 cột độc lập (Đề thi bên phải, bài làm bên trái)"
              className="px-2.5 py-2 bg-blue-50 dark:bg-blue-950/50 hover:bg-blue-100 dark:hover:bg-blue-900/60 text-apple-blue border border-blue-200 dark:border-blue-800 text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-1"
            >
              <Columns className="w-3.5 h-3.5 text-apple-blue" />
              <span>2 Cột</span>
            </button>

            <button
              onClick={onNavigateToFlashcards}
              className="group px-3.5 py-2 bg-gradient-to-r from-apple-blue to-indigo-600 hover:from-apple-blueHover hover:to-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4 text-white" />
              <span>Ôn Thẻ Nhớ</span>
              {dueCount > 0 ? (
                <span className="bg-white text-apple-blue text-[10px] px-1.5 py-0.5 rounded-full font-extrabold shadow-sm">
                  {dueCount}
                </span>
              ) : (
                <span className="bg-white/20 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                  0
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Thông Báo AI Đã Tiếp Nhận Bài Làm Hoặc Đồng Bộ Kế Hoạch */}
      {toastMessage && (
        <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 px-4 py-2.5 rounded-2xl flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 font-medium animate-fadeIn flex-shrink-0 shadow-sm">
          <span>{toastMessage}</span>
          <button
            onClick={() => setToastMessage(null)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 ml-4 font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Frame Trình Chiếu Giao Diện Kế Hoạch & Bài Học: Chiều Cao Toàn Màn Hình Khi Cuộn Xuống */}
      <div className="w-full h-screen min-h-[720px] bg-white dark:bg-[#1c1c1e] rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
        <iframe
          ref={iframeRef}
          src={currentUrl}
          className="w-full h-full border-none"
          title="Digital Garden Study Plan"
        />
      </div>
    </div>
  );
};

export default DailySession;
