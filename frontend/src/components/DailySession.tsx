import React, { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, FlashcardItem } from "../services/api";
import {
  BookOpen,
  RotateCcw,
  ChevronRight,
  Maximize2,
  Minimize2,
  ExternalLink,
  CheckCircle2,
  Trophy,
  Layers,
  GripVertical,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Quartz Garden iFrame Panel
// ---------------------------------------------------------------------------

const QUARTZ_URL = "http://localhost:8088";

interface GardenPanelProps {
  width: number; // percentage 0–100
}

const GardenPanel: React.FC<GardenPanelProps> = ({ width }) => (
  <div
    className="flex flex-col h-full bg-white dark:bg-[#1c1c1e] rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm"
    style={{ width: `${width}%` }}
  >
    {/* Panel header */}
    <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 flex-shrink-0">
      <div className="flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-apple-blue" />
        <span className="text-xs font-bold text-apple-textLight dark:text-apple-textDark">
          Khu Vườn Tri Thức
        </span>
        <span className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">
          Quartz v4
        </span>
      </div>
      <a
        href={QUARTZ_URL}
        target="_blank"
        rel="noopener noreferrer"
        title="Mở trong tab mới"
        className="text-gray-400 hover:text-apple-blue transition"
      >
        <ExternalLink className="w-3.5 h-3.5" />
      </a>
    </div>

    {/* iFrame */}
    <iframe
      src={QUARTZ_URL}
      title="Quartz Digital Garden"
      className="flex-1 w-full border-0"
      // Allow same-origin scripts; sandbox relaxed so Quartz JS works
      sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
    />
  </div>
);

// ---------------------------------------------------------------------------
// Rating Button
// ---------------------------------------------------------------------------

interface RatingButtonProps {
  rating: 1 | 2 | 3 | 4;
  label: string;
  sublabel: string;
  color: string;
  hotkey: string;
  onClick: () => void;
  disabled: boolean;
}

const RatingButton: React.FC<RatingButtonProps> = ({
  rating,
  label,
  sublabel,
  color,
  hotkey,
  onClick,
  disabled,
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    title={`Phím tắt: ${hotkey}`}
    className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition flex flex-col items-center gap-0.5 disabled:opacity-40 ${color}`}
  >
    <span>{label}</span>
    <span className="font-normal opacity-75 text-[10px]">{sublabel}</span>
    <kbd className="mt-0.5 text-[9px] bg-black/10 dark:bg-white/10 px-1 rounded">
      {hotkey}
    </kbd>
  </button>
);

// ---------------------------------------------------------------------------
// Flashcard Panel
// ---------------------------------------------------------------------------

interface FlashcardPanelProps {
  width: number;
}

const FlashcardPanel: React.FC<FlashcardPanelProps> = ({ width }) => {
  const queryClient = useQueryClient();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [sessionDone, setSessionDone] = useState(false);

  const {
    data: cards = [],
    isLoading,
    error,
  } = useQuery<FlashcardItem[]>({
    queryKey: ["flashcards", "due"],
    queryFn: () => api.getDueCards(30),
  });

  const reviewMutation = useMutation({
    mutationFn: ({ cardId, rating }: { cardId: string; rating: number }) =>
      api.reviewCard(cardId, rating),
    onSuccess: () => {
      setIsFlipped(false);
      if (currentIndex + 1 < cards.length) {
        setCurrentIndex((prev) => prev + 1);
      } else {
        queryClient.invalidateQueries({ queryKey: ["flashcards"] });
        setSessionDone(true);
      }
    },
  });

  const handleRate = useCallback(
    (rating: number) => {
      const card = cards[currentIndex];
      if (!card || reviewMutation.isPending) return;
      reviewMutation.mutate({ cardId: card.id, rating });
    },
    [cards, currentIndex, reviewMutation],
  );

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      if (e.code === "Space") {
        e.preventDefault();
        setIsFlipped((prev) => !prev);
      } else if (isFlipped && ["1", "2", "3", "4"].includes(e.key)) {
        e.preventDefault();
        handleRate(parseInt(e.key));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isFlipped, handleRate]);

  // Reset when new cards arrive
  useEffect(() => {
    setCurrentIndex(0);
    setIsFlipped(false);
    setSessionDone(false);
  }, [cards]);

  const card: FlashcardItem | undefined = cards[currentIndex];
  const progress =
    cards.length > 0 ? Math.round((currentIndex / cards.length) * 100) : 0;

  return (
    <div
      className="flex flex-col h-full bg-white dark:bg-[#1c1c1e] rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm"
      style={{ width: `${width}%` }}
    >
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-apple-blue" />
          <span className="text-xs font-bold text-apple-textLight dark:text-apple-textDark">
            Ôn Tập Thẻ Nhớ FSRS
          </span>
        </div>
        {cards.length > 0 && !sessionDone && (
          <span className="text-[11px] font-mono text-apple-subtextLight dark:text-apple-subtextDark">
            {currentIndex + 1} / {cards.length}
          </span>
        )}
      </div>

      {/* Progress bar */}
      {cards.length > 0 && (
        <div className="h-1 bg-gray-100 dark:bg-gray-800 flex-shrink-0">
          <div
            className="h-full bg-apple-blue transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Body */}
      <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-auto">
        {/* Loading */}
        {isLoading && (
          <div className="flex flex-col items-center gap-3 text-apple-subtextLight dark:text-apple-subtextDark">
            <div className="w-8 h-8 border-2 border-apple-blue border-t-transparent rounded-full animate-spin" />
            <p className="text-sm">Đang tải thẻ nhớ...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-center text-red-500 text-sm">
            <p className="font-semibold">Không thể tải thẻ nhớ</p>
            <p className="text-xs mt-1 opacity-75">
              Kiểm tra kết nối tới FastAPI (port 8000)
            </p>
          </div>
        )}

        {/* Session completed */}
        {!isLoading && !error && sessionDone && (
          <div className="flex flex-col items-center gap-4 text-center">
            <Trophy className="w-12 h-12 text-yellow-500" />
            <h3 className="text-lg font-bold text-apple-textLight dark:text-apple-textDark">
              Hoàn thành phiên hôm nay! 🎉
            </h3>
            <p className="text-sm text-apple-subtextLight dark:text-apple-subtextDark">
              Đã ôn tập{" "}
              <span className="font-bold text-apple-blue">{cards.length}</span>{" "}
              thẻ nhớ trong phiên này.
            </p>
            <button
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ["flashcards"] });
                setSessionDone(false);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-apple-blue text-white text-xs font-semibold rounded-xl hover:bg-apple-blueHover transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Tải lại thẻ nhớ
            </button>
          </div>
        )}

        {/* No cards due */}
        {!isLoading && !error && !sessionDone && cards.length === 0 && (
          <div className="flex flex-col items-center gap-3 text-center">
            <CheckCircle2 className="w-10 h-10 text-apple-green" />
            <h3 className="text-base font-bold text-apple-textLight dark:text-apple-textDark">
              Không có thẻ cần ôn hôm nay
            </h3>
            <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark max-w-[200px]">
              Hãy đọc notes trong Khu Vườn Tri Thức bên cạnh, sau đó quay lại
              kiểm tra.
            </p>
          </div>
        )}

        {/* Flashcard */}
        {!isLoading && !error && !sessionDone && card && (
          <div className="w-full flex flex-col gap-4">
            {/* Card body */}
            <div
              onClick={() => setIsFlipped((prev) => !prev)}
              className="relative w-full cursor-pointer select-none"
              style={{ perspective: "1000px" }}
            >
              <div
                className="relative w-full transition-transform duration-500"
                style={{
                  transformStyle: "preserve-3d",
                  transform: isFlipped ? "rotateY(180deg)" : "rotateY(0deg)",
                  minHeight: "180px",
                }}
              >
                {/* Front */}
                <div
                  className="absolute inset-0 flex flex-col items-center justify-center p-5 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-100 dark:border-blue-800/40 rounded-2xl"
                  style={{ backfaceVisibility: "hidden" }}
                >
                  <p className="text-[10px] uppercase tracking-widest text-apple-blue font-bold mb-3">
                    Từ / Khái Niệm
                  </p>
                  <p className="text-center font-bold text-apple-textLight dark:text-apple-textDark text-lg leading-snug">
                    {card.front}
                  </p>
                  {card.tags && card.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3 justify-center">
                      {card.tags
                        .split(",")
                        .map((t) => t.trim())
                        .filter(Boolean)
                        .map((tag) => (
                          <span
                            key={tag}
                            className="text-[9px] bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 px-2 py-0.5 rounded-full font-semibold"
                          >
                            {tag}
                          </span>
                        ))}
                    </div>
                  )}
                  <p className="mt-4 text-[10px] text-apple-subtextLight dark:text-apple-subtextDark animate-pulse">
                    Nhấn Space hoặc click để lật thẻ
                  </p>
                </div>

                {/* Back */}
                <div
                  className="absolute inset-0 flex flex-col items-center justify-center p-5 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-100 dark:border-green-800/40 rounded-2xl"
                  style={{
                    backfaceVisibility: "hidden",
                    transform: "rotateY(180deg)",
                  }}
                >
                  <p className="text-[10px] uppercase tracking-widest text-apple-green font-bold mb-3">
                    Đáp Án / Giải Nghĩa
                  </p>
                  <p className="text-center font-semibold text-apple-textLight dark:text-apple-textDark text-base leading-snug">
                    {card.back}
                  </p>
                </div>
              </div>
            </div>

            {/* Rating buttons — only visible when flipped */}
            <div
              className={`flex gap-2 transition-all duration-300 ${
                isFlipped
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 pointer-events-none translate-y-2"
              }`}
            >
              <RatingButton
                rating={1}
                label="Again"
                sublabel="Quên hoàn toàn"
                color="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-800/40"
                hotkey="1"
                onClick={() => handleRate(1)}
                disabled={reviewMutation.isPending}
              />
              <RatingButton
                rating={2}
                label="Hard"
                sublabel="Rất khó"
                color="bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 hover:bg-orange-100 dark:hover:bg-orange-900/40 border border-orange-200 dark:border-orange-800/40"
                hotkey="2"
                onClick={() => handleRate(2)}
                disabled={reviewMutation.isPending}
              />
              <RatingButton
                rating={3}
                label="Good"
                sublabel="Vừa phải"
                color="bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/40 border border-blue-200 dark:border-blue-800/40"
                hotkey="3"
                onClick={() => handleRate(3)}
                disabled={reviewMutation.isPending}
              />
              <RatingButton
                rating={4}
                label="Easy"
                sublabel="Dễ dàng"
                color="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40 border border-green-200 dark:border-green-800/40"
                hotkey="4"
                onClick={() => handleRate(4)}
                disabled={reviewMutation.isPending}
              />
            </div>

            {/* Hint when not flipped */}
            {!isFlipped && (
              <p className="text-center text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
                Đọc ghi chú bên trái → Nhớ nghĩa → Nhấn{" "}
                <kbd className="bg-gray-100 dark:bg-gray-800 px-1 rounded text-[9px]">
                  Space
                </kbd>{" "}
                để xem đáp án
              </p>
            )}
          </div>
        )}
      </div>

      {/* Footer: next card hint */}
      {card && !sessionDone && (
        <div className="px-4 py-2.5 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between flex-shrink-0">
          <span className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
            Còn lại:{" "}
            <span className="font-bold">{cards.length - currentIndex - 1}</span>{" "}
            thẻ
          </span>
          {cards[currentIndex + 1] && (
            <span className="flex items-center gap-1 text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
              Tiếp: {cards[currentIndex + 1].front.slice(0, 20)}…
              <ChevronRight className="w-3 h-3" />
            </span>
          )}
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Draggable Divider
// ---------------------------------------------------------------------------

interface DividerProps {
  onDrag: (dx: number, containerWidth: number) => void;
}

const Divider: React.FC<DividerProps> = ({ onDrag }) => {
  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      const container = (e.currentTarget as HTMLElement).parentElement!;

      const onMove = (ev: MouseEvent) => {
        onDrag(ev.movementX, container.offsetWidth);
      };
      const onUp = () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
      };
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    },
    [onDrag],
  );

  return (
    <div
      onMouseDown={onMouseDown}
      className="flex-shrink-0 w-2 flex items-center justify-center cursor-col-resize group"
    >
      <div className="w-1 h-12 bg-gray-200 dark:bg-gray-700 rounded-full group-hover:bg-apple-blue transition-colors">
        <GripVertical className="w-3 h-3 text-gray-400 dark:text-gray-600 -ml-1 mt-4 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main DailySession Component
// ---------------------------------------------------------------------------

const DailySession: React.FC = () => {
  // Split ratio: left panel (Quartz) gets `split`%, right (Flashcard) gets rest
  const [split, setSplit] = useState(55);
  const [leftMaximized, setLeftMaximized] = useState(false);
  const [rightMaximized, setRightMaximized] = useState(false);

  const effectiveSplit = leftMaximized ? 96 : rightMaximized ? 4 : split;
  const gardenWidth = effectiveSplit;
  // 2% gap accounted for by the divider element
  const flashcardWidth = 100 - effectiveSplit;

  const handleDrag = useCallback((dx: number, containerWidth: number) => {
    setSplit((prev) => {
      const delta = (dx / containerWidth) * 100;
      return Math.min(80, Math.max(20, prev + delta));
    });
  }, []);

  return (
    <div className="flex flex-col gap-3 h-[calc(100vh-9rem)]">
      {/* Session header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h2 className="text-base font-extrabold text-apple-textLight dark:text-apple-textDark">
            📅 Phiên Học Hôm Nay
          </h2>
          <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark mt-0.5">
            Đọc ghi chú kế hoạch bên trái → Lật thẻ nhớ bên phải để hoàn thành
            ôn tập
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setLeftMaximized((v) => !v);
              setRightMaximized(false);
            }}
            title={leftMaximized ? "Khôi phục" : "Mở rộng Khu Vườn"}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 hover:text-apple-blue border border-gray-200 dark:border-gray-700 rounded-xl transition"
          >
            {leftMaximized ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
            {leftMaximized ? "Thu hẹp" : "Khu Vườn"}
          </button>

          <button
            onClick={() => {
              setRightMaximized((v) => !v);
              setLeftMaximized(false);
            }}
            title={rightMaximized ? "Khôi phục" : "Mở rộng Flashcard"}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 hover:text-apple-blue border border-gray-200 dark:border-gray-700 rounded-xl transition"
          >
            {rightMaximized ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
            {rightMaximized ? "Thu hẹp" : "Thẻ Nhớ"}
          </button>
        </div>
      </div>

      {/* Split layout */}
      <div className="flex flex-1 gap-0 min-h-0">
        <GardenPanel width={gardenWidth} />
        {!leftMaximized && !rightMaximized && (
          <Divider onDrag={handleDrag} />
        )}
        <FlashcardPanel width={flashcardWidth} />
      </div>
    </div>
  );
};

export default DailySession;
