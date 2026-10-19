import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FlashcardReviewer } from "./components/FlashcardReviewer";
import { StatsDashboard } from "./components/StatsDashboard";
import { TestAttemptEditor } from "./components/TestAttemptEditor";
import { RAGSearch } from "./components/RAGSearch";
import DailySession from "./components/DailySession";
import { ConfigSettings } from "./components/ConfigSettings";
import { Logo } from "./components/Logo";
import {
  CalendarDays,
  BookOpen,
  CheckSquare,
  Bot,
  BarChart3,
  Settings,
} from "lucide-react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
    },
  },
});

type Tab = "session" | "flashcards" | "test" | "rag" | "stats" | "config";

const NAV_ITEMS: { id: Tab; icon: React.ReactNode; label: string }[] = [
  {
    id: "session",
    icon: <CalendarDays className="w-3.5 h-3.5" />,
    label: "Phiên Học Hôm Nay",
  },
  {
    id: "flashcards",
    icon: <BookOpen className="w-3.5 h-3.5" />,
    label: "Thẻ Nhớ FSRS",
  },
  {
    id: "test",
    icon: <CheckSquare className="w-3.5 h-3.5" />,
    label: "Luyện Thi & Chấm Bài",
  },
  {
    id: "rag",
    icon: <Bot className="w-3.5 h-3.5" />,
    label: "Hỏi Đáp AI (RAG)",
  },
  {
    id: "stats",
    icon: <BarChart3 className="w-3.5 h-3.5" />,
    label: "Viễn Trắc & Thống Kê",
  },
  {
    id: "config",
    icon: <Settings className="w-3.5 h-3.5" />,
    label: "Cấu Hình & Hệ Thống",
  },
];

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("session");

  return (
    <div
      className={`flex flex-col bg-[#f5f5f7] dark:bg-[#1c1c1e] text-[#1d1d1f] dark:text-[#f5f5f7] ${
        activeTab === "session" ? "h-screen overflow-hidden" : "min-h-screen"
      }`}
    >
      {/* Navigation Header */}
      <header className="backdrop-blur-md bg-white/80 dark:bg-[#1c1c1e]/80 border-b border-gray-200 dark:border-gray-800 transition flex-shrink-0">
        <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
          {/* Brand */}
          <div
            className="flex items-center gap-2.5 flex-shrink-0 cursor-pointer"
            onClick={() => setActiveTab("session")}
            title="Về Phiên Học Hôm Nay"
          >
            <Logo size={34} showText={true} />
          </div>

          {/* Tab Navigation */}
          <nav className="flex items-center gap-0.5 bg-gray-100 dark:bg-gray-800/80 p-1 rounded-2xl overflow-x-auto">
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
                {label}
                {/* "New" badge for the session tab */}
                {id === "session" && activeTab !== "session" && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 bg-apple-blue rounded-full" />
                )}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main
        className={`flex-1 w-full mx-auto px-4 ${
          activeTab === "session"
            ? "max-w-screen-2xl py-2 flex flex-col min-h-0 overflow-hidden"
            : "max-w-6xl py-8"
        }`}
      >
        {activeTab === "session" && (
          <DailySession
            onNavigateToFlashcards={() => setActiveTab("flashcards")}
          />
        )}
        {activeTab === "flashcards" && <FlashcardReviewer />}
        {activeTab === "test" && <TestAttemptEditor />}
        {activeTab === "rag" && <RAGSearch />}
        {activeTab === "stats" && <StatsDashboard />}
        {activeTab === "config" && <ConfigSettings />}
      </main>
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
