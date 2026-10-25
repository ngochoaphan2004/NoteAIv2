import React, { useState, useEffect, useRef } from "react";
import {
  Clock,
  Play,
  Pause,
  RotateCcw,
  Send,
  Copy,
  Download,
  Trash2,
  FileCheck2,
  Sparkles,
  Award,
} from "lucide-react";
import { api, EvaluationResponse } from "../../services/api";

interface IeltsWritingWorkspaceProps {
  taskId?: string;
  targetWords?: number;
  initialMinutes?: number;
  notePath: string;
  title?: string;
  onSubmitted?: (result: EvaluationResponse) => void;
}

export const IeltsWritingWorkspace: React.FC<IeltsWritingWorkspaceProps> = ({
  taskId = "task-1",
  targetWords = 150,
  initialMinutes = 20,
  notePath,
  title,
  onSubmitted,
}) => {
  const effectiveId = `${notePath.replace(/[^a-zA-Z0-9_-]/g, "_")}_${taskId}`;
  const storageTextKey = `noteai_write_${effectiveId}`;
  const storageEvalKey = `noteai_write_eval_${effectiveId}`;
  const storageTimerKey = `noteai_write_timer_${effectiveId}`;

  const [text, setText] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"diff" | "clean" | "rubric">("diff");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  // Timer
  const totalSeconds = initialMinutes * 60;
  const [remainingSeconds, setRemainingSeconds] = useState(totalSeconds);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    try {
      const savedText = localStorage.getItem(storageTextKey);
      if (savedText) setText(savedText);
      else setText("");

      const savedEval = localStorage.getItem(storageEvalKey);
      if (savedEval) setEvaluation(JSON.parse(savedEval));
      else setEvaluation(null);

      const savedTime = sessionStorage.getItem(storageTimerKey);
      if (savedTime && !isNaN(Number(savedTime))) {
        setRemainingSeconds(Number(savedTime));
      } else {
        setRemainingSeconds(totalSeconds);
      }
    } catch (e) {
      console.warn("Lỗi phục hồi bài viết từ LocalStorage:", e);
    }
  }, [effectiveId]);

  useEffect(() => {
    if (isTimerRunning) {
      timerRef.current = window.setInterval(() => {
        setRemainingSeconds((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current!);
            setIsTimerRunning(false);
            sessionStorage.removeItem(storageTimerKey);
            return 0;
          }
          const next = prev - 1;
          sessionStorage.setItem(storageTimerKey, String(next));
          return next;
        });
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isTimerRunning]);

  const handleTextChange = (val: string) => {
    setText(val);
    try {
      localStorage.setItem(storageTextKey, val);
    } catch (e) {}
  };

  const handleStartTimer = () => setIsTimerRunning(true);
  const handlePauseTimer = () => setIsTimerRunning(false);
  const handleResetTimer = () => {
    setIsTimerRunning(false);
    setRemainingSeconds(totalSeconds);
    sessionStorage.removeItem(storageTimerKey);
  };

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  // Word count calculation
  const wordCount = (text.match(/\b[\w'-]+\b/g) || []).length;
  const wordDiff = wordCount - targetWords;

  const handleSubmit = async () => {
    if (!text.trim()) {
      alert("Khung bài làm đang trống! Hãy viết bài trước khi gửi.");
      return;
    }

    try {
      setIsSubmitting(true);
      const result = await api.evaluateAttempt(text, "writing", notePath, taskId);

      setEvaluation(result);
      if (result.diff_html) {
        setActiveTab("diff");
      } else if (result.clean_rewritten_text) {
        setActiveTab("clean");
      } else {
        setActiveTab("rubric");
      }

      try {
        localStorage.setItem(storageEvalKey, JSON.stringify(result));
      } catch (e) {}

      if (onSubmitted) {
        onSubmitted(result);
      }
    } catch (err: any) {
      alert(`Lỗi chấm bài Writing: ${err.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyPrompt = async () => {
    if (!text.trim()) {
      alert("Khung bài làm đang trống!");
      return;
    }
    const spentSec = totalSeconds - remainingSeconds;
    const spentMin = Math.floor(spentSec / 60);
    const spentSecRem = spentSec % 60;

    const promptPayload = [
      `=== 📝 BÀI LÀM IELTS WRITING CẦN CHẤM & GÓP Ý ===`,
      `• Tài liệu: ${notePath}`,
      `• Phần thi: ${title || taskId.toUpperCase()}`,
      `• Số từ: ${wordCount} từ (Mục tiêu: ≥ ${targetWords} từ)`,
      `• Thời gian hoàn thành: ${spentMin} phút ${spentSecRem} giây`,
      `\n--- NỘI DUNG BÀI VIẾT ---\n`,
      text,
      `\n------------------------`,
      `👉 Nhờ bạn nhận xét theo 4 tiêu chí IELTS Writing (TR/TA, CC, LR, GRA) và viết lại bài văn mẫu tự nhiên!`,
    ].join("\n");

    try {
      await navigator.clipboard.writeText(promptPayload);
      setCopyFeedback("Đã chép Prompt!");
      setTimeout(() => setCopyFeedback(null), 3000);
    } catch {
      alert("Không thể tự động chép vào Clipboard.");
    }
  };

  const handleDownloadMd = () => {
    if (!text.trim()) {
      alert("Khung bài làm đang trống!");
      return;
    }
    const md = `# Bài Làm IELTS Writing - ${taskId.toUpperCase()}\n\n- **Ngày làm:** ${new Date().toLocaleDateString("vi-VN")}\n- **Số từ:** ${wordCount} từ\n\n---\n\n${text}\n`;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ielts-writing-${taskId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    if (confirm("Bạn có chắc chắn muốn xóa bài làm này để viết lại từ đầu?")) {
      setText("");
      setEvaluation(null);
      handleResetTimer();
      try {
        localStorage.removeItem(storageTextKey);
        localStorage.removeItem(storageEvalKey);
      } catch (e) {}
    }
  };

  return (
    <div className="my-5 p-4 sm:p-5 bg-white dark:bg-[#1a1d26] border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm space-y-4 transition">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-xs font-bold uppercase tracking-wider bg-purple-600 text-white rounded-full">
            {taskId.toUpperCase()}
          </span>
          <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
            {title || `Mục tiêu: ≥ ${targetWords} từ`}
          </span>
        </div>

        {/* Timer Widget */}
        <div className="flex items-center gap-2 bg-gray-50 dark:bg-gray-800/80 px-3 py-1 rounded-xl border border-gray-200 dark:border-gray-700">
          <Clock className="w-3.5 h-3.5 text-gray-500" />
          <span
            className={`font-mono text-xs font-bold ${
              remainingSeconds <= 120 && remainingSeconds > 0
                ? "text-red-500 animate-pulse"
                : "text-gray-800 dark:text-gray-200"
            }`}
          >
            {formatTimer(remainingSeconds)}
          </span>

          <div className="flex items-center gap-1 ml-1">
            {!isTimerRunning ? (
              <button
                type="button"
                onClick={handleStartTimer}
                className="p-1 hover:text-apple-blue text-gray-600 dark:text-gray-300 transition"
                title="Bắt đầu tính giờ"
              >
                <Play className="w-3 h-3 fill-current" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handlePauseTimer}
                className="p-1 hover:text-amber-500 text-gray-600 dark:text-gray-300 transition"
                title="Tạm dừng"
              >
                <Pause className="w-3 h-3 fill-current" />
              </button>
            )}
            <button
              type="button"
              onClick={handleResetTimer}
              className="p-1 hover:text-red-500 text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition"
              title="Đặt lại đồng hồ"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Editor Textarea */}
      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => handleTextChange(e.target.value)}
          placeholder={`Nhập bài viết ${taskId.toUpperCase()} của bạn tại đây...`}
          rows={10}
          className="w-full p-3.5 bg-gray-50/70 dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700 rounded-xl text-xs sm:text-sm font-sans leading-relaxed text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:border-apple-blue transition resize-y"
        />
      </div>

      {/* Status bar */}
      <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 dark:text-gray-400 gap-2">
        <div className="flex items-center gap-2">
          <span className="font-bold text-gray-900 dark:text-gray-100">
            {wordCount} từ
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
              wordCount === 0
                ? "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
                : wordDiff >= 0
                  ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                  : "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
            }`}
          >
            {wordCount === 0
              ? "Chưa nhập bài"
              : wordDiff >= 0
                ? `Đạt yêu cầu (+${wordDiff} từ)`
                : `Thiếu ${Math.abs(wordDiff)} từ`}
          </span>
        </div>

        <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
          🟢 Tự động lưu LocalStorage
        </span>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-60 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-1.5"
        >
          <Send className="w-3.5 h-3.5" />
          <span>{isSubmitting ? "Đang chấm bài..." : "🚀 Nộp Bài & Nhận Xét 4 Tiêu Chí"}</span>
        </button>

        <button
          type="button"
          onClick={handleCopyPrompt}
          className="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-semibold rounded-xl border border-gray-200 dark:border-gray-700 transition flex items-center gap-1.5"
        >
          <Copy className="w-3.5 h-3.5 text-gray-500" />
          <span>{copyFeedback || "Sao Chép Bài"}</span>
        </button>

        <button
          type="button"
          onClick={handleDownloadMd}
          className="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-semibold rounded-xl border border-gray-200 dark:border-gray-700 transition flex items-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5 text-gray-500" />
          <span>Tải file .md</span>
        </button>

        <button
          type="button"
          onClick={handleClear}
          className="px-3 py-2 text-gray-400 hover:text-red-500 text-xs font-semibold transition ml-auto flex items-center gap-1"
          title="Xóa viết lại từ đầu"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Xóa Khung</span>
        </button>
      </div>

      {/* AI Writing Evaluation Tabs & Display */}
      {evaluation && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800 space-y-3 animate-fadeIn">
          {/* Header Banner */}
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-blue-500/10 border border-purple-500/30 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="p-2 bg-purple-600 text-white rounded-xl shadow-sm">
                <Sparkles className="w-5 h-5" />
              </span>
              <div>
                <div className="text-xs font-bold text-purple-900 dark:text-purple-300">
                  Kết Quả Chấm & Phân Tích IELTS Writing
                </div>
                <div className="text-sm font-extrabold text-gray-900 dark:text-gray-100 mt-0.5">
                  Band Score ước lượng:{" "}
                  <span className="text-purple-600 dark:text-purple-400 text-base">
                    {evaluation.band_score ?? "7.0+"}
                  </span>
                  {evaluation.edits_count !== undefined && (
                    <span className="text-xs font-normal text-gray-500 ml-2">
                      ({evaluation.edits_count} điểm sửa gợi ý)
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Tab Buttons */}
          <div className="flex items-center gap-1.5 border-b border-gray-200 dark:border-gray-800 pb-2">
            {evaluation.diff_html && (
              <button
                type="button"
                onClick={() => setActiveTab("diff")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                  activeTab === "diff"
                    ? "bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-800"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                🔴🟢 Bản Sửa Trực Quan
              </button>
            )}

            {evaluation.clean_rewritten_text && (
              <button
                type="button"
                onClick={() => setActiveTab("clean")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                  activeTab === "clean"
                    ? "bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-800"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                🌟 Bản Viết Lại Hoàn Chỉnh
              </button>
            )}

            {evaluation.feedback && (
              <button
                type="button"
                onClick={() => setActiveTab("rubric")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                  activeTab === "rubric"
                    ? "bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-800"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                📊 Nhận Xét 4 Tiêu Chí IELTS
              </button>
            )}
          </div>

          {/* Tab Panels */}
          {activeTab === "diff" && evaluation.diff_html && (
            <div
              className="p-4 bg-gray-50/80 dark:bg-gray-900/40 rounded-xl border border-gray-200 dark:border-gray-800 text-xs sm:text-sm leading-relaxed"
              dangerouslySetInnerHTML={{ __html: evaluation.diff_html }}
            />
          )}

          {activeTab === "clean" && evaluation.clean_rewritten_text && (
            <div className="p-4 bg-gray-50/80 dark:bg-gray-900/40 rounded-xl border border-gray-200 dark:border-gray-800 text-xs sm:text-sm leading-relaxed whitespace-pre-line text-gray-800 dark:text-gray-200 font-sans">
              {evaluation.clean_rewritten_text}
            </div>
          )}

          {activeTab === "rubric" && evaluation.feedback && (
            <div className="p-4 bg-gray-50/80 dark:bg-gray-900/40 rounded-xl border border-gray-200 dark:border-gray-800 text-xs sm:text-sm leading-relaxed whitespace-pre-line text-gray-800 dark:text-gray-200">
              {evaluation.feedback}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
