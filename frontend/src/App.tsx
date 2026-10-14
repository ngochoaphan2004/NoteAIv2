import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FlashcardReviewer } from "./components/FlashcardReviewer";
import { StatsDashboard } from "./components/StatsDashboard";
import { TestAttemptEditor } from "./components/TestAttemptEditor";
import { RAGSearch } from "./components/RAGSearch";
import DailySession from "./components/DailySession";
import { ConfigSettings } from "./components/ConfigSettings";
import {
  CalendarDays,
  BookOpen,
  CheckSquare,
  Search,
  BarChart3,
  Cpu,
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
    icon: <Search className="w-3.5 h-3.5" />,
    label: "Tra Cứu RAG",
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
    <div className="min-h-screen flex flex-col bg-[#f5f5f7] dark:bg-[#1c1c1e] text-[#1d1d1f] dark:text-[#f5f5f7]">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 dark:bg-[#1c1c1e]/80 border-b border-gray-200 dark:border-gray-800 transition">
        <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <span className="w-7 h-7 rounded-xl bg-apple-blue flex items-center justify-center text-white font-black text-xs shadow-sm">
              N2
            </span>
            <div className="hidden sm:block">
              <h1 className="text-sm font-extrabold tracking-tight leading-none">
                NoteAI.v2
              </h1>
              <p className="text-[9px] text-apple-subtextLight dark:text-apple-subtextDark uppercase tracking-wider font-semibold">
                Local Autonomous PKM
              </p>
            </div>
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
        className={`flex-1 w-full mx-auto px-4 py-4 ${
          activeTab === "session" ? "max-w-screen-2xl" : "max-w-6xl py-8"
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

      {/* Hardware & Network Status Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-apple-cardDark py-3 text-[11px] text-apple-subtextLight dark:text-apple-subtextDark">
        <div className="max-w-screen-2xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-apple-green animate-pulse" />
              PostgreSQL 16 :5433
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-apple-green animate-pulse" />
              Qdrant :6333
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-apple-blue animate-pulse" />
              FastAPI :8000
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" />
              Quartz :8088
            </span>
          </div>

          <div className="flex items-center gap-1 text-[11px] font-mono">
            <Cpu className="w-3.5 h-3.5 text-apple-blue" />
            FastEmbed (CPU ONNX AVX2) | GPU VRAM Safe
          </div>
        </div>
      </footer>
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
