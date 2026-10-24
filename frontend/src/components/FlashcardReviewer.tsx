import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, FlashcardItem } from "../services/api";
import {
  RotateCcw,
  CheckCircle,
  Volume2,
  Sparkles,
  AlertCircle,
} from "lucide-react";

const renderFormattedText = (text: string) => {
  if (!text) return null;
  const clean = text.replace(/<br\s*\/?>/gi, "\n");
  const lines = clean.split("\n");

  return lines.map((line, lineIdx) => {
    const trimmed = line.trim();
    if (!trimmed) return <div key={lineIdx} className="h-2" />;

    const parts = line.split(/(_[^_]+_|\*\*[^*]+\*\*)/g);
    const lineContent = parts.map((part, partIdx) => {
      if (part.startsWith("_") && part.endsWith("_") && part.length > 2) {
        return (
          <span key={partIdx} className="font-semibold text-apple-blue dark:text-blue-400">
            {part.slice(1, -1)}
          </span>
        );
      }
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
        return (
          <strong key={partIdx} className="font-bold text-apple-textLight dark:text-apple-textDark">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });

    const isBullet = trimmed.startsWith("•") || trimmed.startsWith("-");
    const isSectionHeader =
      trimmed.includes("Ví dụ & Collocations:") ||
      trimmed.includes("Collocations & Ví Dụ:");

    if (isSectionHeader) {
      return (
        <div
          key={lineIdx}
          className="font-bold text-xs uppercase tracking-wider text-apple-subtextLight dark:text-apple-subtextDark mt-3.5 mb-1.5 border-b border-gray-100 dark:border-gray-800 pb-1 flex items-center gap-1.5"
        >
          <span>📌</span>
          <span>Collocations & Ngữ Cảnh:</span>
        </div>
      );
    }

    if (lineIdx === 0 && !isBullet) {
      return (
        <div
          key={lineIdx}
          className="text-base font-bold text-emerald-700 dark:text-emerald-400 mb-2 leading-snug"
        >
          {lineContent}
        </div>
      );
    }

    return (
      <div
        key={lineIdx}
        className={
          isBullet
            ? "pl-2 py-0.5 text-xs text-gray-700 dark:text-gray-300 leading-relaxed"
            : "py-0.5 text-xs text-gray-700 dark:text-gray-300 leading-relaxed"
        }
      >
        {lineContent}
      </div>
    );
  });
};

export const FlashcardReviewer: React.FC = () => {
  const queryClient = useQueryClient();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  const {
    data: rawCards = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["flashcards", "due"],
    queryFn: () => api.getDueCards(50),
  });

  // Lớp bảo vệ bổ sung: Lọc bỏ bất kỳ thẻ nào có front bị lẫn bullet hoặc HTML
  const cards = rawCards.filter(
    (c) => c.front && !c.front.startsWith("•") && !c.front.includes("<br>")
  );

  const reviewMutation = useMutation({
    mutationFn: ({ cardId, rating }: { cardId: string; rating: number }) =>
      api.reviewCard(cardId, rating),
    onSuccess: () => {
      setIsFlipped(false);
      if (currentIndex + 1 < cards.length) {
        setCurrentIndex((prev) => prev + 1);
      } else {
        queryClient.invalidateQueries({ queryKey: ["flashcards"] });
      }
    },
  });

  // Xử lý phím tắt
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault();
        setIsFlipped((prev) => !prev);
      } else if (isFlipped && ["1", "2", "3", "4"].includes(e.key)) {
        e.preventDefault();
        const rating = parseInt(e.key);
        if (cards[currentIndex]) {
          reviewMutation.mutate({ cardId: cards[currentIndex].id, rating });
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFlipped, currentIndex, cards, reviewMutation]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-apple-subtextLight dark:text-apple-subtextDark">
        <div className="w-8 h-8 border-4 border-apple-blue border-t-transparent rounded-full animate-spin mb-4" />
        <p>Đang tải danh sách thẻ đến hạn từ cơ sở dữ liệu FSRS...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-2xl text-center">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-2" />
        <p className="text-red-700 dark:text-red-300 font-medium">
          Lỗi kết nối Backend FSRS
        </p>
        <p className="text-xs text-red-500 mt-1">{(error as Error).message}</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (!cards.length || currentIndex >= cards.length) {
    return (
      <div className="p-12 text-center bg-white dark:bg-apple-cardDark rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm max-w-lg mx-auto">
        <CheckCircle className="w-16 h-16 text-apple-green mx-auto mb-4" />
        <h3 className="text-xl font-bold text-apple-textLight dark:text-apple-textDark mb-2">
          Tuyệt vời! Bạn đã hoàn thành phiên ôn tập hôm nay
        </h3>
        <p className="text-sm text-apple-subtextLight dark:text-apple-subtextDark mb-6">
          Toàn bộ các thẻ đến hạn đã được cập nhật lại theo công thức toán học
          DSR của FSRS v4.
        </p>
        <button
          onClick={() => {
            setCurrentIndex(0);
            setIsFlipped(false);
            refetch();
          }}
          className="px-6 py-3 bg-apple-blue text-white rounded-xl text-sm font-semibold hover:bg-apple-blueHover transition inline-flex items-center gap-2 shadow-sm"
        >
          <RotateCcw className="w-4 h-4" /> Làm mới lại phiên học
        </button>
      </div>
    );
  }

  const currentCard: FlashcardItem = cards[currentIndex];

  return (
    <div className="max-w-xl mx-auto">
      {/* Thanh tiến độ */}
      <div className="flex items-center justify-between text-xs text-apple-subtextLight dark:text-apple-subtextDark mb-3 px-1 font-medium">
        <span>
          Thẻ {currentIndex + 1} / {cards.length}
        </span>
        <span className="flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-apple-orange" />
          FSRS v4 Scheduler ({currentCard.state})
        </span>
      </div>

      <div className="w-full bg-gray-200 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden mb-6">
        <div
          className="bg-apple-blue h-full transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / cards.length) * 100}%` }}
        />
      </div>

      {/* Thẻ Flashcard 3D */}
      <div
        onClick={() => setIsFlipped(!isFlipped)}
        className="w-full min-h-[340px] bg-white dark:bg-apple-cardDark border border-gray-200 dark:border-gray-800 rounded-3xl p-8 shadow-sm hover:shadow-md transition cursor-pointer flex flex-col justify-between relative group select-none"
      >
        {/* Mặt Trước */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-full text-xs font-semibold uppercase tracking-wider">
              {currentCard.tags?.split(",")[0] || "IELTS"}
            </span>
            <span className="text-xs text-apple-subtextLight dark:text-apple-subtextDark">
              Nhấn{" "}
              <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-[10px] font-mono border">
                Space
              </kbd>{" "}
              để lật
            </span>
          </div>

          <div className="text-center py-6">
            <h2 className="text-4xl font-extrabold text-apple-textLight dark:text-apple-textDark tracking-tight mb-2">
              {currentCard.front ? currentCard.front.replace(/\*\*([^*]+)\*\*/g, "$1").replace(/`([^`]+)`/g, "$1").trim() : ""}
            </h2>
            {currentCard.ipa && (
              <p className="text-apple-subtextLight dark:text-apple-subtextDark italic text-base">
                {currentCard.ipa}
              </p>
            )}
            {currentCard.part_of_speech && (
              <p className="text-xs font-semibold text-apple-blue uppercase tracking-wider mt-1">
                {currentCard.part_of_speech}
              </p>
            )}
          </div>
        </div>

        {/* Mặt Sau (Hiện khi Flipped) */}
        {isFlipped ? (
          <div className="border-t border-gray-100 dark:border-gray-800 pt-5 mt-2 animate-fadeIn">
            {currentCard.synonyms && (
              <div className="mb-3 text-xs">
                <span className="font-semibold text-apple-subtextLight dark:text-apple-subtextDark uppercase mr-1">
                  Đồng nghĩa:
                </span>
                <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                  {currentCard.synonyms}
                </span>
              </div>
            )}
            <div className="text-sm text-apple-textLight dark:text-apple-textDark leading-relaxed">
              {renderFormattedText(currentCard.back)}
            </div>
          </div>
        ) : (
          <div className="text-center text-xs text-apple-subtextLight dark:text-apple-subtextDark font-medium py-2">
            (Bấm vào thẻ hoặc nhấn phím Space để xem nghĩa & ví dụ)
          </div>
        )}
      </div>

      {/* 4 Nút đánh giá FSRS v4 (Responsive 2 cột trên mobile, 4 cột trên desktop) */}
      {isFlipped && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 mt-4 sm:mt-6">
          <button
            onClick={() =>
              reviewMutation.mutate({ cardId: currentCard.id, rating: 1 })
            }
            className="flex flex-col items-center justify-center p-2.5 sm:p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-2xl hover:bg-red-100 dark:hover:bg-red-900/50 transition group"
          >
            <span className="text-xs font-bold text-red-600 dark:text-red-400 group-hover:scale-105 transition">
              Again (1)
            </span>
            <span className="text-[11px] text-red-500 font-mono mt-0.5">
              {currentCard.preview_intervals?.again || "1m"}
            </span>
          </button>

          <button
            onClick={() =>
              reviewMutation.mutate({ cardId: currentCard.id, rating: 2 })
            }
            className="flex flex-col items-center justify-center p-2.5 sm:p-3.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 rounded-2xl hover:bg-amber-100 dark:hover:bg-amber-900/50 transition group"
          >
            <span className="text-xs font-bold text-amber-600 dark:text-amber-400 group-hover:scale-105 transition">
              Hard (2)
            </span>
            <span className="text-[11px] text-amber-500 font-mono mt-0.5">
              {currentCard.preview_intervals?.hard || "1d"}
            </span>
          </button>

          <button
            onClick={() =>
              reviewMutation.mutate({ cardId: currentCard.id, rating: 3 })
            }
            className="flex flex-col items-center justify-center p-2.5 sm:p-3.5 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 rounded-2xl hover:bg-blue-100 dark:hover:bg-blue-900/50 transition group"
          >
            <span className="text-xs font-bold text-apple-blue dark:text-apple-blueDark group-hover:scale-105 transition">
              Good (3)
            </span>
            <span className="text-[11px] text-blue-500 font-mono mt-0.5">
              {currentCard.preview_intervals?.good || "3d"}
            </span>
          </button>

          <button
            onClick={() =>
              reviewMutation.mutate({ cardId: currentCard.id, rating: 4 })
            }
            className="flex flex-col items-center justify-center p-2.5 sm:p-3.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-2xl hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition group"
          >
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 group-hover:scale-105 transition">
              Easy (4)
            </span>
            <span className="text-[11px] text-emerald-500 font-mono mt-0.5">
              {currentCard.preview_intervals?.easy || "7d"}
            </span>
          </button>
        </div>
      )}
    </div>
  );
};
