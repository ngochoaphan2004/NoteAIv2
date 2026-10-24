import React, { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FlashcardReviewer } from "./components/FlashcardReviewer";
import { StatsDashboard } from "./components/StatsDashboard";
import { RAGSearch } from "./components/RAGSearch";
import DailySession from "./components/DailySession";
import { ConfigSettings } from "./components/ConfigSettings";
import { Logo } from "./components/Logo";
import { LoginPage } from "./components/LoginPage";
import {
  api,
  getAuthToken,
  getStoredUser,
} from "./services/api";
import {
  CalendarDays,
  BookOpen,
  Bot,
  BarChart3,
  Settings,
  LogOut,
  User,
} from "lucide-react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
    },
  },
});

type Tab = "session" | "flashcards" | "rag" | "stats" | "config";

const NAV_ITEMS: { id: Tab; icon: React.ReactNode; label: string; mobileLabel: string }[] = [
  {
    id: "session",
    icon: <CalendarDays className="w-4 h-4" />,
    label: "Phiên Học Hôm Nay",
    mobileLabel: "Hôm Nay",
  },
  {
    id: "flashcards",
    icon: <BookOpen className="w-4 h-4" />,
    label: "Thẻ Nhớ FSRS",
    mobileLabel: "Thẻ Nhớ",
  },
  {
    id: "rag",
    icon: <Bot className="w-4 h-4" />,
    label: "Hỏi Đáp AI (RAG)",
    mobileLabel: "Hỏi Đáp",
  },
  {
    id: "stats",
    icon: <BarChart3 className="w-4 h-4" />,
    label: "Viễn Trắc & Thống Kê",
    mobileLabel: "Thống Kê",
  },
  {
    id: "config",
    icon: <Settings className="w-4 h-4" />,
    label: "Cấu Hình & Hệ Thống",
    mobileLabel: "Cài Đặt",
  },
];

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("session");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() =>
    Boolean(getAuthToken())
  );
  const [currentUser, setCurrentUser] = useState<{
    username: string;
    role: string;
  } | null>(() => getStoredUser());

  // Kiểm tra tính hợp lệ của token khi khởi động
  useEffect(() => {
    if (isAuthenticated) {
      api.verifyAuth().then((isValid) => {
        if (!isValid) {
          setIsAuthenticated(false);
          setCurrentUser(null);
        }
      });
    }
  }, [isAuthenticated]);

  const handleLoginSuccess = (user: { username: string; role: string }) => {
    setIsAuthenticated(true);
    setCurrentUser(user);
    setActiveTab("session");
  };

  const handleLogout = async () => {
    if (window.confirm("Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?")) {
      await api.logout();
      setIsAuthenticated(false);
      setCurrentUser(null);
    }
  };

  // Nếu chưa đăng nhập, hiển thị màn hình Login
  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#f5f5f7] dark:bg-[#1c1c1e] text-[#1d1d1f] dark:text-[#f5f5f7]">
      {/* Navigation Header */}
      <header className="backdrop-blur-md bg-white/80 dark:bg-[#1c1c1e]/80 border-b border-gray-200 dark:border-gray-800 transition sticky top-0 z-40">
        <div className="max-w-screen-2xl mx-auto px-3 sm:px-4 h-14 flex items-center justify-between gap-2 sm:gap-4">
          {/* Brand */}
          <div
            className="flex items-center gap-2 flex-shrink-0 cursor-pointer"
            onClick={() => setActiveTab("session")}
            title="Về Phiên Học Hôm Nay"
          >
            <Logo size={32} showText={true} />
          </div>

          {/* Desktop Tab Navigation (Ẩn trên mobile < 768px để dùng Bottom Bar) */}
          <nav className="hidden md:flex items-center gap-0.5 bg-gray-100 dark:bg-gray-800/80 p-1 rounded-2xl">
            {NAV_ITEMS.map(({ id, icon, label }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === id
                    ? "bg-white dark:bg-apple-cardDark text-apple-blue shadow-sm"
                    : "text-apple-subtextLight dark:text-apple-subtextDark hover:text-apple-textLight"
                } ${id === "session" && activeTab !== "session" ? "relative" : ""}`}
              >
                {icon}
                <span>{label}</span>
                {/* Badge thông báo trên tab session */}
                {id === "session" && activeTab !== "session" && (
                  <span className="w-2 h-2 bg-apple-blue rounded-full" />
                )}
              </button>
            ))}
          </nav>

          {/* User Info & Logout Button */}
          <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
            <div className="flex items-center gap-1 px-2 py-1 sm:px-2.5 sm:py-1 bg-gray-100 dark:bg-gray-800 rounded-xl text-xs font-medium text-gray-700 dark:text-gray-300">
              <User className="w-3.5 h-3.5 text-apple-blue shrink-0" />
              <span className="max-w-[70px] sm:max-w-none truncate">{currentUser?.username || "admin"}</span>
            </div>

            <button
              onClick={handleLogout}
              className="p-1.5 sm:px-2.5 sm:py-1 bg-gray-100 hover:bg-red-50 dark:bg-gray-800 dark:hover:bg-red-950/40 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded-xl text-xs font-semibold transition flex items-center gap-1 border border-transparent hover:border-red-200 dark:hover:border-red-900"
              title="Đăng xuất khỏi hệ thống"
            >
              <LogOut className="w-3.5 h-3.5 shrink-0" />
              <span className="hidden sm:inline">Đăng xuất</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container (pb-24 trên mobile để không bị Bottom Bar che nội dung) */}
      <main
        className={`flex-1 w-full mx-auto px-3 sm:px-4 py-3 sm:py-6 pb-24 md:pb-8 ${
          activeTab === "session" ? "max-w-screen-2xl" : "max-w-6xl py-4 sm:py-8"
        }`}
      >
        {activeTab === "session" && (
          <DailySession
            onNavigateToFlashcards={() => setActiveTab("flashcards")}
          />
        )}
        {activeTab === "flashcards" && <FlashcardReviewer />}
        {activeTab === "rag" && <RAGSearch />}
        {activeTab === "stats" && <StatsDashboard />}
        {activeTab === "config" && <ConfigSettings />}
      </main>

      {/* Mobile Bottom Navigation Bar (Apple HIG Style - Tự động hiển thị trên điện thoại hoặc khi thu nhỏ cửa sổ trình duyệt < 768px) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 dark:bg-[#1c1c1e]/95 backdrop-blur-xl border-t border-gray-200/90 dark:border-gray-800/90 px-1.5 py-1.5 flex items-center justify-around shadow-[0_-4px_20px_rgba(0,0,0,0.06)] dark:shadow-[0_-4px_20px_rgba(0,0,0,0.4)]">
        {NAV_ITEMS.map(({ id, icon, mobileLabel }) => {
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex flex-col items-center justify-center py-1 px-1.5 rounded-xl transition-all relative flex-1 max-w-[72px] ${
                isActive
                  ? "text-apple-blue font-bold scale-105"
                  : "text-apple-subtextLight dark:text-apple-subtextDark hover:text-gray-900 dark:hover:text-gray-100"
              }`}
            >
              <div
                className={`p-1 rounded-xl transition ${
                  isActive ? "bg-blue-50 dark:bg-blue-950/70" : ""
                }`}
              >
                {icon}
              </div>
              <span className="text-[10px] mt-0.5 tracking-tight font-medium leading-none">
                {mobileLabel}
              </span>
              {id === "session" && !isActive && (
                <span className="absolute top-1 right-2.5 w-2 h-2 bg-apple-blue rounded-full ring-2 ring-white dark:ring-[#1c1c1e]" />
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
