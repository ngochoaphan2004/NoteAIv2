import React, { useState, useEffect, useRef } from "react";
import {
  Clock,
  Play,
  Pause,
  RotateCcw,
  Send,
  Copy,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Award,
  ChevronDown,
  ChevronUp,
  Check,
  X,
  Lightbulb,
} from "lucide-react";
import { api, EvaluationResponse } from "../../services/api";

interface IeltsAnswerSheetProps {
  sheetId?: string;
  startQ?: number;
  endQ?: number;
  initialMinutes?: number;
  notePath: string;
  skill?: string;
  title?: string;
  onSubmitted?: (result: EvaluationResponse) => void;
}

export const IeltsAnswerSheet: React.FC<IeltsAnswerSheetProps> = ({
  sheetId,
  startQ = 1,
  endQ = 20,
  initialMinutes = 20,
  notePath,
  skill = "listening",
  title,
  onSubmitted,
}) => {
  const effectiveSheetId =
    sheetId || notePath.replace(/[^a-zA-Z0-9_-]/g, "_") || "default_sheet";

  const storageAnswersKey = `noteai_answers_${effectiveSheetId}`;
  const storageEvalKey = `noteai_eval_${effectiveSheetId}`;
  const storageTimerKey = `noteai_timer_${effectiveSheetId}`;

  // State
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
  const [showResultDetails, setShowResultDetails] = useState(true);

  // Timer State
  const totalSeconds = initialMinutes * 60;
  const [remainingSeconds, setRemainingSeconds] = useState(totalSeconds);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const timerRef = useRef<number | null>(null);

  // Restore answers & eval on load or sheetId change
  useEffect(() => {
    try {
      const savedAnswers = localStorage.getItem(storageAnswersKey);
      if (savedAnswers) {
        setAnswers(JSON.parse(savedAnswers));
      } else {
        setAnswers({});
      }

      const savedEval = localStorage.getItem(storageEvalKey);
      if (savedEval) {
        setEvaluation(JSON.parse(savedEval));
      } else {
        setEvaluation(null);
      }

      const savedTime = sessionStorage.getItem(storageTimerKey);
      if (savedTime && !isNaN(Number(savedTime))) {
        setRemainingSeconds(Number(savedTime));
      } else {
        setRemainingSeconds(totalSeconds);
      }
    } catch (e) {
      console.warn("Lỗi phục hồi trạng thái từ LocalStorage:", e);
    }
  }, [effectiveSheetId]);

  // Timer interval
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

  const handleInputChange = (qNum: number, value: string) => {
    const updated = { ...answers, [String(qNum)]: value };
    setAnswers(updated);
    try {
      localStorage.setItem(storageAnswersKey, JSON.stringify(updated));
    } catch (e) {
      console.warn("Không thể lưu đáp án vào LocalStorage:", e);
    }
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    currentIndex: number,
  ) => {
    if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      const nextInput = document.getElementById(
        `ielts-input-${effectiveSheetId}-${currentIndex + 1}`,
      );
      if (nextInput) {
        nextInput.focus();
        (nextInput as HTMLInputElement).select();
      }
    }
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

  // Stats
  const filledCount = Object.keys(answers).filter(
    (k) => Number(k) >= startQ && Number(k) <= endQ && answers[k]?.trim(),
  ).length;
  const totalCount = endQ - startQ + 1;

  // Submit to backend
  const handleSubmit = async () => {
    const lines: string[] = [];
    for (let q = startQ; q <= endQ; q++) {
      const val = (answers[String(q)] || "").trim();
      if (val) {
        lines.push(`${q} ${val}`);
      }
    }

    if (lines.length === 0) {
      alert("Bảng đáp án đang trống! Vui lòng điền ít nhất một câu trước khi nộp.");
      return;
    }

    try {
      setIsSubmitting(true);
      const attemptText = lines.join("\n");
      const result = await api.evaluateAttempt(attemptText, skill, notePath);

      // Save evaluation to LocalStorage
      setEvaluation(result);
      setShowResultDetails(true);
      try {
        localStorage.setItem(storageEvalKey, JSON.stringify(result));
      } catch (e) {
        console.warn("Không thể lưu kết quả chấm vào LocalStorage:", e);
      }

      if (onSubmitted) {
        onSubmitted(result);
      }
    } catch (err: any) {
      alert(`Lỗi khi nộp bài và chấm điểm: ${err.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Copy shorthand
  const handleCopyShorthand = async () => {
    const lines: string[] = [];
    for (let q = startQ; q <= endQ; q++) {
      const val = (answers[String(q)] || "").trim();
      if (val) {
        lines.push(`${q} ${val}`);
      }
    }
    if (lines.length === 0) {
      alert("Bảng đáp án đang trống!");
      return;
    }

    const shorthand = [
      `=== 📋 BÀI LÀM IELTS SHORTHAND ===`,
      `• Tài liệu: ${notePath}`,
      `• Kỹ năng: ${skill.toUpperCase()}`,
      `• Tiến độ: ${lines.length}/${totalCount} câu`,
      `\n--- ĐÁP ÁN ---\n`,
      lines.join("\n"),
    ].join("\n");

    try {
      await navigator.clipboard.writeText(shorthand);
      setCopyFeedback("Đã chép Shorthand!");
      setTimeout(() => setCopyFeedback(null), 3000);
    } catch {
      alert("Không thể tự động chép vào Clipboard.");
    }
  };

  // Clear sheet
  const handleClearSheet = () => {
    if (
      confirm(
        "Bạn có chắc muốn xóa sạch toàn bộ câu trả lời và kết quả chấm của bài này?",
      )
    ) {
      setAnswers({});
      setEvaluation(null);
      handleResetTimer();
      try {
        localStorage.removeItem(storageAnswersKey);
        localStorage.removeItem(storageEvalKey);
      } catch (e) {}
    }
  };

  // Generate question numbers array
  const qNumbers: number[] = [];
  for (let i = startQ; i <= endQ; i++) {
    qNumbers.push(i);
  }

  // Map evaluation questions for easy lookup
  const evalMap = new Map<number, any>();
  if (evaluation?.questions) {
    for (const q of evaluation.questions) {
      evalMap.set(q.question_number, q);
    }
  }

  return (
    <div className="my-5 p-4 sm:p-5 bg-white dark:bg-[#1a1d26] border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm space-y-4 transition">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-xs font-bold uppercase tracking-wider bg-apple-blue text-white rounded-full">
            {skill.toUpperCase()}
          </span>
          <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
            {title || `Câu ${startQ} – ${endQ}`}
          </span>
        </div>

        {/* Timer Widget */}
        <div className="flex items-center gap-2 bg-gray-50 dark:bg-gray-800/80 px-3 py-1 rounded-xl border border-gray-200 dark:border-gray-700">
          <Clock className="w-3.5 h-3.5 text-gray-500" />
          <span
            className={`font-mono text-xs font-bold ${
              remainingSeconds <= 60 && remainingSeconds > 0
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

      {/* Progress & Save indicator */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-1.5 font-medium">
          <span>Tiến độ:</span>
          <span className="font-bold text-apple-blue">
            {filledCount} / {totalCount} câu đã điền
          </span>
        </div>
        <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
          🟢 Tự động lưu LocalStorage
        </span>
      </div>

      {/* Answer Inputs Grid */}
      <div className="grid grid-cols-[repeat(auto-fill,minmax(115px,1fr))] gap-2 sm:gap-2.5">
        {qNumbers.map((qNum, idx) => {
          const evalItem = evalMap.get(qNum);
          const hasCorrect = evalItem?.is_correct === true;
          const hasWrong = evalItem?.is_correct === false;

          return (
            <div
              key={qNum}
              className={`flex items-center rounded-xl border px-2 py-1.5 transition ${
                hasCorrect
                  ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-400/60 dark:border-emerald-800"
                  : hasWrong
                    ? "bg-red-50 dark:bg-red-950/30 border-red-400/60 dark:border-red-800"
                    : "bg-gray-50/80 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 focus-within:border-apple-blue"
              }`}
            >
              <span
                className={`w-6 text-xs font-bold text-center select-none ${
                  hasCorrect
                    ? "text-emerald-600 dark:text-emerald-400"
                    : hasWrong
                      ? "text-red-600 dark:text-red-400"
                      : "text-gray-400 dark:text-gray-500"
                }`}
              >
                {qNum}
              </span>
              <input
                id={`ielts-input-${effectiveSheetId}-${idx}`}
                type="text"
                value={answers[String(qNum)] || ""}
                onChange={(e) => handleInputChange(qNum, e.target.value)}
                onKeyDown={(e) => handleKeyDown(e, idx)}
                placeholder="..."
                autoComplete="off"
                spellCheck="false"
                className="w-full bg-transparent px-1.5 py-0.5 text-xs font-semibold text-gray-900 dark:text-gray-100 placeholder-gray-400 outline-none"
              />
              {hasCorrect && (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
              )}
              {hasWrong && (
                <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-2 pt-2">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-4 py-2 bg-gradient-to-r from-apple-blue to-indigo-600 hover:from-apple-blueHover hover:to-indigo-700 disabled:opacity-60 text-white text-xs font-bold rounded-xl shadow-sm transition flex items-center gap-1.5"
        >
          <Send className="w-3.5 h-3.5" />
          <span>{isSubmitting ? "Đang chấm điểm..." : "🚀 Nộp Bài & Chấm Điểm Trực Tiếp"}</span>
        </button>

        <button
          type="button"
          onClick={handleCopyShorthand}
          className="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-semibold rounded-xl border border-gray-200 dark:border-gray-700 transition flex items-center gap-1.5"
        >
          <Copy className="w-3.5 h-3.5 text-gray-500" />
          <span>{copyFeedback || "Sao Chép Shorthand"}</span>
        </button>

        <button
          type="button"
          onClick={handleClearSheet}
          className="px-3 py-2 text-gray-400 hover:text-red-500 text-xs font-semibold transition ml-auto flex items-center gap-1"
          title="Xóa làm lại từ đầu"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Xóa Bảng</span>
        </button>
      </div>

      {/* AI Evaluation Result Card */}
      {evaluation && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800 space-y-3 animate-fadeIn">
          {/* Banner */}
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-blue-500/10 border border-emerald-500/30 flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="p-2 bg-emerald-600 text-white rounded-xl shadow-sm">
                <Award className="w-5 h-5" />
              </span>
              <div>
                <div className="text-xs font-bold text-emerald-800 dark:text-emerald-300">
                  Kết Quả Chấm Điểm Cambridge 18
                </div>
                <div className="text-sm font-extrabold text-gray-900 dark:text-gray-100 mt-0.5">
                  Đúng:{" "}
                  <span className="text-emerald-600 dark:text-emerald-400">
                    {evaluation.score_fraction || `${filledCount}/${totalCount}`}
                  </span>{" "}
                  &bull; Band Score:{" "}
                  <span className="text-apple-blue font-black text-base">
                    {evaluation.band_score ?? "N/A"}
                  </span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowResultDetails(!showResultDetails)}
              className="text-xs font-medium text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 flex items-center gap-1 mt-1"
            >
              <span>{showResultDetails ? "Thu gọn" : "Xem chi tiết"}</span>
              {showResultDetails ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
          </div>

          {/* Feedback & Detailed comparison table */}
          {showResultDetails && (
            <div className="space-y-4 pt-2">
              {evaluation.feedback && (
                <div className="p-3.5 bg-blue-50/70 dark:bg-blue-950/25 border border-blue-200/80 dark:border-blue-900/60 border-l-4 border-l-blue-500 rounded-xl text-xs sm:text-[13px] text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-line shadow-2xs">
                  <div className="flex items-center gap-1.5 font-bold text-blue-700 dark:text-blue-300 mb-1.5">
                    <Lightbulb className="w-4 h-4 text-blue-500 shrink-0" />
                    <span>Nhận Xét & Đối Soát Từ AI</span>
                  </div>
                  {evaluation.feedback}
                </div>
              )}

              {/* Table */}
              {evaluation.questions && evaluation.questions.length > 0 && (
                <div className="table-container my-3 overflow-hidden rounded-xl border border-gray-200/90 dark:border-gray-800/90 shadow-2xs bg-white dark:bg-[#151720]">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800 text-left text-xs sm:text-[13px] font-sans border-collapse">
                      <thead className="bg-gray-50/90 dark:bg-[#1a1d27] text-gray-700 dark:text-gray-200 font-bold uppercase tracking-wider text-[11px] border-b border-gray-200 dark:border-gray-800">
                        <tr>
                          <th className="py-3 px-3.5 w-14 min-w-[56px] text-center whitespace-nowrap">Câu</th>
                          <th className="py-3 px-3.5 min-w-[130px] text-center whitespace-nowrap">Bạn Đã Chọn</th>
                          <th className="py-3 px-3.5 min-w-[140px] text-center whitespace-nowrap">Đáp Án Chuẩn</th>
                          <th className="py-3 px-3.5 min-w-[95px] text-center whitespace-nowrap">Trạng Thái</th>
                          <th className="py-3 px-3.5 min-w-[300px] text-left">Giải Thích & Bẫy</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-800/60 bg-white dark:bg-[#151720]">
                        {evaluation.questions.map((q) => (
                          <tr key={q.question_number} className="border-b border-gray-100 dark:border-gray-800/60 hover:bg-gray-50/80 dark:hover:bg-gray-800/35 transition-colors">
                            <td className="py-3 px-3.5 font-bold text-center text-gray-900 dark:text-gray-100">
                              {q.question_number}
                            </td>
                            <td className="py-3 px-3.5 text-center">
                              {q.user_answer ? (
                                <code className="px-1.5 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800/90 text-blue-700 dark:text-blue-300 font-mono text-[12px] font-semibold border border-gray-200/80 dark:border-gray-700/70">
                                  {q.user_answer}
                                </code>
                              ) : (
                                <span className="text-gray-400 dark:text-gray-500">—</span>
                              )}
                            </td>
                            <td className="py-3 px-3.5 text-center">
                              {q.correct_answer ? (
                                <code className="px-1.5 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-mono text-[12px] font-bold border border-emerald-200/70 dark:border-emerald-800/70">
                                  {q.correct_answer}
                                </code>
                              ) : (
                                <span className="text-gray-400 dark:text-gray-500">—</span>
                              )}
                            </td>
                            <td className="py-3 px-3.5 text-center">
                              {q.is_correct ? (
                                <span className="inline-flex items-center justify-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/70 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-900/60 shadow-2xs whitespace-nowrap">
                                  <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                                  <span>Đúng</span>
                                </span>
                              ) : (
                                <span className="inline-flex items-center justify-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/70 dark:text-rose-300 border border-rose-200/80 dark:border-rose-900/60 shadow-2xs whitespace-nowrap">
                                  <X className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                                  <span>Sai</span>
                                </span>
                              )}
                            </td>
                            <td className="py-3 px-3.5 text-gray-700 dark:text-gray-300 text-xs sm:text-[13px] leading-relaxed">
                              {q.trap_type && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold bg-blue-50/90 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200/70 dark:border-blue-900/60 mr-1.5 shadow-2xs select-none">
                                  {q.trap_type}
                                </span>
                              )}
                              {q.explanation || "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
