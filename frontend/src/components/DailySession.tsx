import React, { useState, useEffect, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  api,
  FlashcardItem,
  EvaluationResponse,
} from "../services/api";
import {
  BookOpen,
  Calendar,
  RotateCw,
  ArrowRight,
  Compass,
  CheckCircle2,
  Sparkles,
  Zap,
  CheckCheck,
  PanelLeftClose,
  PanelLeft,
  PanelRightClose,
  PanelRight,
  Columns,
  FileQuestion,
} from "lucide-react";
import { GardenSidebar } from "./garden/GardenSidebar";
import { NoteViewer } from "./garden/NoteViewer";
import { RightTocSidebar } from "./garden/RightTocSidebar";
import { SplitExamWorkspace } from "./garden/SplitExamWorkspace";

interface DailySessionProps {
  onNavigateToFlashcards: () => void;
  routeNotePath?: string;
  onSelectNotePath?: (path: string, replace?: boolean) => void;
}

export const DailySession: React.FC<DailySessionProps> = ({
  onNavigateToFlashcards,
  routeNotePath,
  onSelectNotePath,
}) => {
  const queryClient = useQueryClient();

  // Selected note path (ưu tiên routeNotePath từ URL router, sau đó đến LocalStorage)
  const [currentNotePath, setCurrentNotePath] = useState<string>(() => {
    if (routeNotePath) return routeNotePath;
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("noteai_last_note_path");
      if (saved) return saved;
    }
    return "plans/week-01/index.md";
  });

  // Đồng bộ khi routeNotePath từ URL thay đổi (F5 reload, popstate trình duyệt, hoặc nhấp link)
  useEffect(() => {
    if (routeNotePath && routeNotePath !== currentNotePath) {
      setCurrentNotePath(routeNotePath);
      try {
        localStorage.setItem("noteai_last_note_path", routeNotePath);
      } catch (e) {}
    }
  }, [routeNotePath]);

  // Cập nhật nhẹ nhàng URL trình duyệt khi vào root hoặc /session
  useEffect(() => {
    if (window.location.pathname === "/" || window.location.pathname === "/session") {
      if (currentNotePath && onSelectNotePath) {
        onSelectNotePath(currentNotePath, true);
      }
    }
  }, []);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isRightTocOpen, setIsRightTocOpen] = useState(true);
  const [isSplitMode, setIsSplitMode] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  // Lấy thông tin nhiệm vụ hôm nay từ AI Plan Service
  const { data: todayPlan, refetch: refetchTodayPlan } = useQuery({
    queryKey: ["plans", "today"],
    queryFn: () => api.getTodayPlan(),
    staleTime: 1000 * 60 * 2,
  });

  // Lấy số thẻ cần ôn FSRS
  const { data: dueCards = [] } = useQuery<FlashcardItem[]>({
    queryKey: ["flashcards", "due"],
    queryFn: () => api.getDueCards(50),
    staleTime: 1000 * 60,
  });

  // Tải nội dung bài học Markdown trực tiếp từ SSOT qua REST API
  const {
    data: currentNote,
    isLoading: isNoteLoading,
    isError: isNoteError,
    error: noteError,
    refetch: refetchNote,
  } = useQuery({
    queryKey: ["content", "note", currentNotePath],
    queryFn: () => api.getNote(currentNotePath),
    staleTime: 1000 * 30, // 30s cache
  });

  // Phát hiện xem note hiện tại có chứa khối đề thi hoặc <details> không
  const hasExamDetails = useMemo(() => {
    if (!currentNote) return false;
    if (currentNote.exam_metadata?.has_exam) return true;
    return /<details[\s\S]*?>[\s\S]*?<\/details>/i.test(currentNote.raw_content || "");
  }, [currentNote]);

  // Phím tắt Alt+S chuyển đổi chế độ thi chia đôi 2 cột
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === "s" || e.key === "S")) {
        e.preventDefault();
        if (hasExamDetails) {
          setIsSplitMode((prev) => !prev);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [hasExamDetails]);

  // Tự động tắt split mode khi chuyển sang note khác
  useEffect(() => {
    setIsSplitMode(false);
  }, [currentNotePath]);

  const handleSelectNote = (rawPath: string) => {
    let clean = rawPath.replace(/\\/g, "/").replace(/^\/+|\/+$/g, "");
    if (clean.startsWith("content/")) {
      clean = clean.slice("content/".length);
    }
    if (!clean.endsWith(".md") && !clean.includes("#")) {
      clean = `${clean}.md`;
    }
    setCurrentNotePath(clean);
    try {
      localStorage.setItem("noteai_last_note_path", clean);
    } catch (e) {}
    if (onSelectNotePath) {
      onSelectNotePath(clean, false);
    }
  };

  const handleTestSubmitted = (result: EvaluationResponse) => {
    const scoreStr = result.score_fraction
      ? `(${result.score_fraction} câu đúng • Band ${result.band_score})`
      : "";
    setToastMessage(
      `🎉 AI đã chấm điểm và lưu kết quả bài làm thành công! ${scoreStr}`,
    );

    // Tự động làm mới plan và note content
    queryClient.invalidateQueries({ queryKey: ["plans", "today"] });
    queryClient.invalidateQueries({ queryKey: ["content", "note", currentNotePath] });

    setTimeout(() => {
      setToastMessage(null);
    }, 7000);
  };

  const handleAutoSync = async () => {
    try {
      setIsSyncing(true);
      const res = await api.syncPlans();
      await refetchTodayPlan();
      await refetchNote();
      setToastMessage(
        `⚡ AI đã tự động đồng bộ kế hoạch theo ngày ${res.today} và tiến độ cá nhân!`,
      );
      setTimeout(() => setToastMessage(null), 5000);
    } catch (err: any) {
      alert(`Lỗi đồng bộ kế hoạch: ${err.message || err}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const quickNavLinks = [
    {
      label: "Tuần 1",
      desktopLabel: "Kế Hoạch Tuần 1",
      path: "plans/week-01/index.md",
      icon: <Calendar className="w-3.5 h-3.5 text-apple-blue" />,
      badge: "Hiện tại",
    },
    {
      label: "Tất cả",
      desktopLabel: "Tất cả kế hoạch",
      path: "plans/index.md",
      icon: <Compass className="w-3.5 h-3.5 text-apple-blue" />,
    },
    {
      label: "Lộ trình 5.0 → 7.5",
      desktopLabel: "Lộ trình 5.0 → 7.5",
      path: "roadmap-5.0-to-7.5.md",
      icon: <Sparkles className="w-3.5 h-3.5 text-purple-500" />,
    },
    {
      label: "Tài nguyên",
      desktopLabel: "Tài Nguyên & Công Cụ",
      path: "resources-learning-tools.md",
      icon: <BookOpen className="w-3.5 h-3.5 text-emerald-500" />,
    },
  ];

  const dueCount = dueCards.length;

  return (
    <div className="flex flex-col gap-3 pb-8 relative">
      {/* AI Today's Task Banner */}
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
                  type="button"
                  onClick={() => handleSelectNote(todayPlan.link)}
                  className="px-3 py-1 bg-apple-blue hover:bg-apple-blueHover text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center gap-1"
                >
                  <span>Vào bài học ngay</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )
            )}

            <button
              type="button"
              onClick={handleAutoSync}
              disabled={isSyncing}
              title="Kích hoạt AI tự động đối soát tiến độ và ngày tháng"
              className="px-2.5 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:text-apple-blue text-xs font-medium rounded-lg border border-gray-200 dark:border-gray-700 transition flex items-center gap-1"
            >
              <RotateCw
                className={`w-3 h-3 ${isSyncing ? "animate-spin text-apple-blue" : ""}`}
              />
              <span>{isSyncing ? "Đang đồng bộ..." : "AI Tự Đồng Bộ"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Navigation & Action Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2.5 bg-white dark:bg-[#1c1c1e] p-2.5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm transition">
        {/* Quick Nav links */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar scrollbar-none py-0.5">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:text-apple-blue hover:bg-gray-100 dark:hover:bg-gray-800 transition flex items-center gap-1.5 text-xs font-semibold mr-1 flex-shrink-0"
            title="Đóng / Mở Cây Thư Mục"
          >
            {isSidebarOpen ? (
              <PanelLeftClose className="w-4 h-4 text-apple-blue" />
            ) : (
              <PanelLeft className="w-4 h-4 text-apple-blue" />
            )}
            <span className="hidden sm:inline">Explorer</span>
          </button>

          {quickNavLinks.map((item) => {
            const isActive = currentNotePath === item.path;
            return (
              <button
                key={item.path}
                type="button"
                onClick={() => handleSelectNote(item.path)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 whitespace-nowrap flex-shrink-0 ${
                  isActive
                    ? "bg-apple-blue text-white shadow-sm"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                }`}
              >
                {item.icon}
                <span className="hidden sm:inline">{item.desktopLabel}</span>
                <span className="sm:hidden">{item.label}</span>
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

        {/* Action Controls */}
        <div className="flex items-center gap-1.5 justify-end flex-shrink-0">
          {/* Nút Chế Độ Thi Chia 2 Cột Độc Lập */}
          {hasExamDetails && (
            <button
              type="button"
              onClick={() => setIsSplitMode(!isSplitMode)}
              title={
                isSplitMode
                  ? "Thoát chế độ 2 cột (Esc / Alt+S)"
                  : "Bật chế độ thi 2 cột độc lập (Alt+S)"
              }
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 border shadow-sm ${
                isSplitMode
                  ? "bg-apple-blue text-white border-apple-blue hover:bg-apple-blueHover"
                  : "bg-blue-50/80 dark:bg-blue-950/40 text-apple-blue border-blue-200 dark:border-blue-900/60 hover:bg-apple-blue hover:text-white"
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>{isSplitMode ? "Thoát 2 Cột" : "Chia 2 Cột"}</span>
            </button>
          )}

          {/* Nút Ẩn / Hiện Mục Lục Trang Bên Phải */}
          {!isSplitMode && currentNote?.headings && currentNote.headings.length > 0 && (
            <button
              type="button"
              onClick={() => setIsRightTocOpen(!isRightTocOpen)}
              title={isRightTocOpen ? "Ẩn thanh mục lục trang bên phải" : "Hiện thanh mục lục trang bên phải"}
              className={`p-1.5 rounded-xl border transition ${
                isRightTocOpen
                  ? "bg-apple-blue/10 text-apple-blue border-apple-blue/30"
                  : "text-gray-500 hover:text-apple-blue hover:bg-gray-100 dark:hover:bg-gray-800 border-gray-200 dark:border-gray-700"
              }`}
            >
              {isRightTocOpen ? (
                <PanelRightClose className="w-4 h-4" />
              ) : (
                <PanelRight className="w-4 h-4" />
              )}
            </button>
          )}

          <button
            type="button"
            onClick={() => refetchNote()}
            title="Làm mới nội dung tài liệu"
            className="p-1.5 text-gray-500 hover:text-apple-blue hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition border border-gray-200 dark:border-gray-700"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={onNavigateToFlashcards}
            className="group px-3 py-1.5 bg-gradient-to-r from-apple-blue to-indigo-600 hover:from-apple-blueHover hover:to-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-1.5"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-white" />
            <span>Ôn Thẻ Nhớ</span>
            {dueCount > 0 ? (
              <span className="bg-white text-apple-blue text-[10px] px-1.5 py-0.2 rounded-full font-extrabold shadow-sm">
                {dueCount}
              </span>
            ) : (
              <span className="bg-white/20 text-white text-[10px] px-1.5 py-0.2 rounded-full">
                0
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Toast Notification */}
      {toastMessage && (
        <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 px-4 py-2.5 rounded-2xl flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 font-medium animate-fadeIn flex-shrink-0 shadow-sm">
          <span>{toastMessage}</span>
          <button
            type="button"
            onClick={() => setToastMessage(null)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 ml-4 font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Digital Garden Workspace Layout */}
      {isSplitMode && currentNote ? (
        <SplitExamWorkspace
          note={currentNote}
          onNavigateNote={handleSelectNote}
          onSubmitted={handleTestSubmitted}
          onExit={() => setIsSplitMode(false)}
        />
      ) : (
        <div className="w-full bg-white dark:bg-[#1a1d26] rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm flex items-start">
          {/* Sidebar Explorer */}
          {isSidebarOpen && (
            <GardenSidebar
              isOpen={isSidebarOpen}
              currentPath={currentNotePath}
              onSelectNote={handleSelectNote}
              headings={currentNote?.headings}
              onClose={() => setIsSidebarOpen(false)}
            />
          )}

          {/* Note Content Viewer */}
          <main className="flex-1 min-w-0 bg-white dark:bg-[#1a1d26]">
            {isNoteLoading ? (
              <div className="flex flex-col items-center justify-center py-24 space-y-3">
                <RotateCw className="w-6 h-6 animate-spin text-apple-blue" />
                <p className="text-xs text-gray-500">Đang đọc tài liệu Markdown...</p>
              </div>
            ) : isNoteError ? (
              <div className="flex flex-col items-center justify-center py-20 px-4 text-center space-y-3">
                <FileQuestion className="w-10 h-10 text-gray-400" />
                <div className="text-sm font-bold text-gray-800 dark:text-gray-200">
                  Không thể tải tài liệu
                </div>
                <p className="text-xs text-gray-500 max-w-md">
                  {(noteError as any)?.message || `Không tìm thấy file "${currentNotePath}"`}
                </p>
                <button
                  type="button"
                  onClick={() => handleSelectNote("plans/week-01/index.md")}
                  className="px-3 py-1.5 bg-apple-blue text-white rounded-xl text-xs font-semibold shadow-sm hover:bg-apple-blueHover transition"
                >
                  Quay về Kế Hoạch Tuần 1
                </button>
              </div>
            ) : currentNote ? (
              <NoteViewer
                note={currentNote}
                onNavigateNote={handleSelectNote}
                onSubmitted={handleTestSubmitted}
                onOpenSplitExam={() => setIsSplitMode(true)}
              />
            ) : null}
          </main>

          {/* Right Sidebar: Table of Contents */}
          {isRightTocOpen && currentNote?.headings && currentNote.headings.length > 0 && (
            <RightTocSidebar
              headings={currentNote.headings}
              isOpen={isRightTocOpen}
              onToggle={() => setIsRightTocOpen(!isRightTocOpen)}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default DailySession;
