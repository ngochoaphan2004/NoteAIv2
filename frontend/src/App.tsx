import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FlashcardReviewer } from './components/FlashcardReviewer';
import { StatsDashboard } from './components/StatsDashboard';
import { TestAttemptEditor } from './components/TestAttemptEditor';
import { RAGSearch } from './components/RAGSearch';
import { BookOpen, CheckSquare, Search, BarChart3, ExternalLink, Cpu } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
    },
  },
});

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'flashcards' | 'test' | 'rag' | 'stats'>('flashcards');

  return (
    <div className="min-h-screen flex flex-col bg-[#f5f5f7] dark:bg-[#1c1c1e] text-[#1d1d1f] dark:text-[#f5f5f7]">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 dark:bg-[#1c1c1e]/80 border-b border-gray-200 dark:border-gray-800 transition">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-xl bg-apple-blue flex items-center justify-center text-white font-black text-sm shadow-sm">
              N2
            </span>
            <div>
              <h1 className="text-base font-extrabold tracking-tight">NoteAI.v2</h1>
              <p className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark uppercase tracking-wider font-semibold">
                Local Autonomous PKM
              </p>
            </div>
          </div>

          {/* Tab Navigation */}
          <nav className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800/80 p-1 rounded-2xl">
            <button
              onClick={() => setActiveTab('flashcards')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
                activeTab === 'flashcards'
                  ? 'bg-white dark:bg-apple-cardDark text-apple-blue shadow-sm'
                  : 'text-apple-subtextLight dark:text-apple-subtextDark hover:text-apple-textLight'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" /> Thẻ Nhớ FSRS
            </button>

            <button
              onClick={() => setActiveTab('test')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
                activeTab === 'test'
                  ? 'bg-white dark:bg-apple-cardDark text-apple-blue shadow-sm'
                  : 'text-apple-subtextLight dark:text-apple-subtextDark hover:text-apple-textLight'
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5" /> Luyện Thi & Chấm Bài
            </button>

            <button
              onClick={() => setActiveTab('rag')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
                activeTab === 'rag'
                  ? 'bg-white dark:bg-apple-cardDark text-apple-blue shadow-sm'
                  : 'text-apple-subtextLight dark:text-apple-subtextDark hover:text-apple-textLight'
              }`}
            >
              <Search className="w-3.5 h-3.5" /> Tra Cứu RAG
            </button>

            <button
              onClick={() => setActiveTab('stats')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
                activeTab === 'stats'
                  ? 'bg-white dark:bg-apple-cardDark text-apple-blue shadow-sm'
                  : 'text-apple-subtextLight dark:text-apple-subtextDark hover:text-apple-textLight'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" /> Viễn Trắc & Thống Kê
            </button>
          </nav>

          {/* Liên kết sang Quartz v4 Static Garden */}
          <a
            href="http://localhost:8088"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-700 dark:text-gray-300 hover:text-apple-blue transition border border-gray-200 dark:border-gray-700 rounded-xl"
          >
            Digital Garden <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        {activeTab === 'flashcards' && <FlashcardReviewer />}
        {activeTab === 'test' && <TestAttemptEditor />}
        {activeTab === 'rag' && <RAGSearch />}
        {activeTab === 'stats' && <StatsDashboard />}
      </main>

      {/* Hardware & Network Status Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-apple-cardDark py-4 text-[11px] text-apple-subtextLight dark:text-apple-subtextDark">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-apple-green animate-pulse" />
              PostgreSQL 16 (Port 5433)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-apple-green animate-pulse" />
              Qdrant (Port 6333)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-apple-blue animate-pulse" />
              FastAPI (Port 8000)
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
