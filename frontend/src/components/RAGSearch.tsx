import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, AskResponse, ContextSource } from "../services/api";
import {
  MessageSquare,
  Sparkles,
  Bot,
  FileText,
  ChevronDown,
  ChevronUp,
  RotateCw,
  Database,
  ShieldCheck,
  Send,
  HelpCircle,
  Clock,
  Layers,
} from "lucide-react";

const PRESET_QUESTIONS = [
  "Chủ đề bài đọc Cam 18 Test 1 Reading Passage 3 là gì?",
  "Kế hoạch học tập Tuần 1 gồm những nội dung và phiên luyện tập nào?",
  "Từ vựng 'vulnerable' và 'struggle' có phát âm, nghĩa và collocations ra sao?",
  "Những bẫy âm và lưu ý trong bài thi Cambridge 18 Test 1 Listening?",
  "Lộ trình học tập từ 5.0 lên 7.5 chia làm mấy giai đoạn?",
];

export const RAGSearch: React.FC = () => {
  const [question, setQuestion] = useState(PRESET_QUESTIONS[0]);
  const [topK, setTopK] = useState(4);
  const [qaResult, setQaResult] = useState<AskResponse | null>(null);
  const [showSources, setShowSources] = useState(true);
  const [expandedChunk, setExpandedChunk] = useState<number | null>(null);

  // Mutation gọi API Hỏi Đáp RAG
  const askMutation = useMutation({
    mutationFn: () => api.askRAG(question, topK),
    onSuccess: (data) => {
      setQaResult(data);
      setShowSources(true);
    },
    onError: (err: any) => {
      alert(`Lỗi hỏi đáp RAG: ${err.message}`);
    },
  });

  // Mutation lập chỉ mục lại Qdrant Vector DB
  const reindexMutation = useMutation({
    mutationFn: () => api.reindexRAG(),
    onSuccess: (data) => {
      alert(
        `✅ Lập chỉ mục thành công: ${data.files_indexed} tài liệu Markdown (${data.total_chunks} đoạn ngữ nghĩa) đã được nạp vào Qdrant!`
      );
    },
    onError: (err: any) => {
      alert(`Lỗi re-index: ${err.message}`);
    },
  });

  const handleAsk = () => {
    if (!question.trim() || askMutation.isPending) return;
    askMutation.mutate();
  };

  const handleSelectPreset = (q: string) => {
    setQuestion(q);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Khung Hỏi Đáp Chính */}
      <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-apple-textLight dark:text-apple-textDark flex items-center gap-2">
              <Bot className="w-5 h-5 text-apple-blue" />
              <span>Hỏi Đáp Kho Tri Thức (RAG Q&A Engine)</span>
            </h2>
            <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark mt-1">
              Câu hỏi &rarr; FastEmbed (CPU ONNX) &rarr; Qdrant Vector DB &rarr; Top K Ngữ Cảnh &rarr; LLM Grounded Generation
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => reindexMutation.mutate()}
              disabled={reindexMutation.isPending}
              className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-apple-subtextLight dark:text-apple-subtextDark rounded-xl text-xs font-semibold transition flex items-center gap-1.5 disabled:opacity-50"
              title="Quét lại toàn bộ file .md trong content/ và nạp vector mới vào Qdrant"
            >
              <Database className="w-3.5 h-3.5" />
              <span>{reindexMutation.isPending ? "Đang index..." : "Lập Chỉ Mục Lại"}</span>
            </button>
          </div>
        </div>

        {/* Ô Nhập Câu Hỏi & Tùy Chọn Top K */}
        <div className="space-y-2">
          <div className="relative">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
              placeholder="Đặt câu hỏi về bài thi IELTS, từ vựng, ngữ pháp hoặc lộ trình học tập..."
              className="w-full p-4 pr-12 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl text-sm text-apple-textLight dark:text-apple-textDark focus:outline-none focus:ring-2 focus:ring-apple-blue transition"
            />
            <button
              onClick={handleAsk}
              disabled={askMutation.isPending || !question.trim()}
              className="absolute right-3.5 bottom-4 p-2 bg-apple-blue text-white rounded-xl hover:bg-apple-blueHover transition shadow-sm disabled:opacity-40"
              title="Gửi câu hỏi"
            >
              {askMutation.isPending ? (
                <RotateCw className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* Controls: Top-K & Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-apple-subtextLight dark:text-apple-subtextDark">
              <Layers className="w-3.5 h-3.5" />
              <span>Trích xuất Top K ngữ cảnh:</span>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="px-2 py-1 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg font-semibold text-apple-blue"
              >
                <option value={2}>2 đoạn</option>
                <option value={3}>3 đoạn</option>
                <option value={4}>4 đoạn (Chuẩn)</option>
                <option value={6}>6 đoạn</option>
                <option value={8}>8 đoạn</option>
              </select>
            </div>

            <button
              onClick={handleAsk}
              disabled={askMutation.isPending || !question.trim()}
              className="px-5 py-2 bg-apple-blue text-white rounded-xl font-bold hover:bg-apple-blueHover transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              {askMutation.isPending ? (
                <>
                  <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  <span>AI Đang Phân Tích...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Hỏi Đáp AI</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Gợi Ý Câu Hỏi Nhanh (Preset Chips) */}
        <div className="pt-2 border-t border-gray-100 dark:border-gray-800">
          <div className="text-[11px] font-semibold text-apple-subtextLight dark:text-apple-subtextDark uppercase tracking-wider mb-2 flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-apple-blue" />
            <span>Gợi Ý Câu Hỏi Nhanh:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {PRESET_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectPreset(q)}
                className={`text-xs px-3 py-1.5 rounded-xl border transition text-left ${
                  question === q
                    ? "bg-blue-50 dark:bg-blue-950/40 border-apple-blue text-apple-blue font-semibold"
                    : "bg-gray-50 dark:bg-gray-800/60 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300"
                }`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Kết Quả Phản Hồi Từ AI (Grounded Answer) */}
      {qaResult && (
        <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-6 animate-fadeIn">
          {/* Header Câu Trả Lời */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-gray-100 dark:border-gray-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-apple-blue to-indigo-600 flex items-center justify-center text-white shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-apple-textLight dark:text-apple-textDark">
                  Câu Trả Lời Từ AI
                </h3>
                <p className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark">
                  {qaResult.model_used ? `Mô hình: ${qaResult.model_used}` : "Grounded AI Engine"} &bull; {qaResult.sources.length} trích đoạn ngữ cảnh
                </p>
              </div>
            </div>

            {/* Banner Ràng Buộc Grounded Prompt */}
            <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-full text-[11px] text-emerald-700 dark:text-emerald-300 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Chỉ dùng ngữ cảnh cung cấp &bull; Không bịa đặt</span>
            </div>
          </div>

          {/* Nội Dung Câu Trả Lời */}
          <div className="prose dark:prose-invert max-w-none text-sm text-apple-textLight dark:text-apple-textDark leading-relaxed whitespace-pre-line bg-gray-50/70 dark:bg-gray-900/40 p-5 rounded-2xl border border-gray-100 dark:border-gray-800">
            {qaResult.answer}
          </div>

          {/* Danh Sách Ngữ Cảnh Đối Soát (Top-K Sources Accordion) */}
          {qaResult.sources.length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-apple-textLight dark:text-apple-textDark uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-apple-blue" />
                  <span>Ngữ Cảnh Trích Xuất Đối Soát (Top {qaResult.sources.length}):</span>
                </h4>
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="text-xs text-apple-blue hover:underline flex items-center gap-1 font-semibold"
                >
                  <span>{showSources ? "Thu gọn ngữ cảnh" : "Xem nguồn ngữ cảnh"}</span>
                  {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              </div>

              {showSources && (
                <div className="space-y-2.5">
                  {qaResult.sources.map((source, idx) => {
                    const isExpanded = expandedChunk === idx;
                    return (
                      <div
                        key={idx}
                        className="p-4 bg-gray-50 dark:bg-gray-900/60 rounded-2xl border border-gray-200/80 dark:border-gray-800 text-xs transition"
                      >
                        <div
                          className="flex items-center justify-between cursor-pointer"
                          onClick={() => setExpandedChunk(isExpanded ? null : idx)}
                        >
                          <div className="flex items-center gap-2 font-semibold text-apple-blue">
                            <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center text-[10px] font-bold">
                              {idx + 1}
                            </span>
                            <span>{source.source_file}</span>
                            <span className="text-gray-400 font-normal">&gt;</span>
                            <span className="text-gray-700 dark:text-gray-300 font-medium">
                              {source.heading}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded-full font-mono text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-apple-blue border border-blue-200 dark:border-blue-900">
                              Độ tương đồng: {(source.score * 100).toFixed(1)}%
                            </span>
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5 text-gray-400" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
                            )}
                          </div>
                        </div>

                        {/* Đoạn Trích Ngữ Cảnh */}
                        <div className={`mt-2.5 pt-2.5 border-t border-gray-200/50 dark:border-gray-800 ${isExpanded ? "" : "line-clamp-3"}`}>
                          <p className="text-[11px] font-mono leading-relaxed text-apple-subtextLight dark:text-apple-subtextDark whitespace-pre-line">
                            {source.content}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RAGSearch;
