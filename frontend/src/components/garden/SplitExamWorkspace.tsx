import React, { useState, useEffect, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeKatex from "rehype-katex";
import {
  Columns,
  Maximize2,
  ZoomIn,
  ZoomOut,
  X,
  BookOpen,
  FileText,
  Volume2,
} from "lucide-react";
import { IeltsAnswerSheet } from "./IeltsAnswerSheet";
import { IeltsWritingWorkspace } from "./IeltsWritingWorkspace";
import { CustomAudioPlayer } from "./CustomAudioPlayer";
import {
  MarkdownBlockquote,
  MarkdownTable,
  MarkdownThead,
  MarkdownTbody,
  MarkdownTr,
  MarkdownTh,
  MarkdownTd,
  MarkdownCode,
  MarkdownUl,
  MarkdownOl,
  MarkdownLi,
} from "./markdownComponents";
import { NoteDetailResponse, EvaluationResponse } from "../../services/api";

interface SplitExamWorkspaceProps {
  note: NoteDetailResponse;
  onNavigateNote: (path: string) => void;
  onSubmitted?: (result: EvaluationResponse) => void;
  onExit: () => void;
  initialSectionIndex?: number;
}

interface ExamSection {
  id: string;
  summary: string;
  body: string;
  fullTag: string;
}

export const SplitExamWorkspace: React.FC<SplitExamWorkspaceProps> = ({
  note,
  onNavigateNote,
  onSubmitted,
  onExit,
  initialSectionIndex = 0,
}) => {
  const [activeSectionIdx, setActiveSectionIdx] = useState(initialSectionIndex);
  const [zoom, setZoom] = useState(95); // 60% to 160%
  const [splitRatio, setSplitRatio] = useState<50 | 40 | 60>(50); // Left column width %

  // Trích xuất các khối <details> chứa đề thi/ảnh từ nội dung Markdown
  const { sections, leftMarkdown } = useMemo(() => {
    let raw = note.raw_content.replace(/^---\s*[\r\n]+[\s\S]*?[\r\n]+---\s*[\r\n]*/, "");

    // Chuyển đổi Wikilinks [[target|label]]
    raw = raw.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, target, label) => {
      const text = (label || target).trim();
      let link = target.trim();
      if (!link.endsWith(".md") && !link.includes("#")) {
        link = `${link}.md`;
      }
      return `[${text}](${link})`;
    });

    const detailsRegex = /<details[\s\S]*?>([\s\S]*?)<\/details>/gi;
    const extracted: ExamSection[] = [];
    let match: RegExpExecArray | null;

    let modifiedLeft = raw;

    while ((match = detailsRegex.exec(raw)) !== null) {
      const full = match[0];
      const inner = match[1];
      const summaryMatch = inner.match(/<summary[\s\S]*?>([\s\S]*?)<\/summary>/i);
      const summary = summaryMatch
        ? summaryMatch[1].replace(/<[^>]+>/g, "").trim()
        : `Tài Liệu Đề Thi ${extracted.length + 1}`;
      const body = inner.replace(/<summary[\s\S]*?<\/summary>/i, "").trim();

      const sec: ExamSection = {
        id: `sec-${extracted.length}`,
        summary,
        body,
        fullTag: full,
      };
      extracted.push(sec);
    }

    // Ở cột trái (Bài làm), thay thế khối <details> đang được chiếu sang cột phải bằng thông báo ngắn
    if (extracted.length > 0) {
      extracted.forEach((sec, idx) => {
        const replacement =
          idx === activeSectionIdx
            ? `\n\n> 📖 **ĐỀ BÀI: ${sec.summary}** đang được chiếu trực tiếp tại **Cột Phải**. Bạn có thể vừa xem đề vừa điền câu trả lời ở cột này.\n\n`
            : "";
        modifiedLeft = modifiedLeft.replace(sec.fullTag, replacement);
      });
    }

    return { sections: extracted, leftMarkdown: modifiedLeft };
  }, [note.raw_content, activeSectionIdx]);

  // Phím tắt Esc để thoát, Alt+S để chuyển đổi
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onExit();
      } else if (e.altKey && (e.key === "s" || e.key === "S")) {
        e.preventDefault();
        onExit();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onExit]);

  const activeSection = sections[activeSectionIdx] || sections[0];

  return (
    <div className="w-full flex flex-col h-[calc(100vh-140px)] min-h-[600px] bg-white dark:bg-[#1a1d26] rounded-2xl border border-gray-200 dark:border-gray-800 shadow-lg overflow-hidden select-text animate-fadeIn">
      {/* Exam Split Topbar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2 bg-gray-50/90 dark:bg-[#14171f]/90 border-b border-gray-200 dark:border-gray-800 backdrop-blur-md gap-2 flex-shrink-0">
        {/* Left Side: Mode badge and note title */}
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-apple-blue text-white shadow-sm">
            <Columns className="w-3.5 h-3.5" />
            <span>Phòng Thi 2 Cột Độc Lập</span>
          </span>
          <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 hidden md:inline truncate max-w-xs">
            {note.title}
          </span>
        </div>

        {/* Center / Section Tabs if multiple */}
        {sections.length > 1 && (
          <div className="flex items-center gap-1 bg-gray-200/60 dark:bg-gray-800/60 p-0.5 rounded-lg">
            {sections.map((sec, idx) => (
              <button
                key={sec.id}
                type="button"
                onClick={() => setActiveSectionIdx(idx)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                  idx === activeSectionIdx
                    ? "bg-white dark:bg-[#1c1c1e] text-apple-blue shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900"
                }`}
              >
                {sec.summary.replace(/^(📄|📜|🎧|📖)\s*/, "").slice(0, 25)}
              </button>
            ))}
          </div>
        )}

        {/* Right Side: Ratio & Zoom Controls & Exit */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Split Ratio */}
          <div className="flex items-center bg-gray-200/60 dark:bg-gray-800/60 p-0.5 rounded-lg text-xs font-semibold">
            <button
              type="button"
              onClick={() => setSplitRatio(50)}
              title="Chia đều 50:50"
              className={`px-2 py-0.5 rounded transition ${
                splitRatio === 50
                  ? "bg-white dark:bg-[#1c1c1e] text-apple-blue shadow-sm font-bold"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900"
              }`}
            >
              50:50
            </button>
            <button
              type="button"
              onClick={() => setSplitRatio(40)}
              title="Bài làm 40% - Đề thi 60%"
              className={`px-2 py-0.5 rounded transition ${
                splitRatio === 40
                  ? "bg-white dark:bg-[#1c1c1e] text-apple-blue shadow-sm font-bold"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900"
              }`}
            >
              40:60
            </button>
            <button
              type="button"
              onClick={() => setSplitRatio(60)}
              title="Bài làm 60% - Đề thi 40%"
              className={`px-2 py-0.5 rounded transition ${
                splitRatio === 60
                  ? "bg-white dark:bg-[#1c1c1e] text-apple-blue shadow-sm font-bold"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900"
              }`}
            >
              60:40
            </button>
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center gap-1 bg-gray-200/60 dark:bg-gray-800/60 p-0.5 rounded-lg text-xs">
            <button
              type="button"
              onClick={() => setZoom((z) => Math.max(60, z - 10))}
              title="Thu nhỏ ảnh đề bài"
              className="p-1 hover:text-apple-blue rounded text-gray-600 dark:text-gray-300"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="px-1 text-[11px] font-mono font-semibold text-gray-700 dark:text-gray-300 min-w-[36px] text-center">
              {zoom}%
            </span>
            <button
              type="button"
              onClick={() => setZoom((z) => Math.min(160, z + 10))}
              title="Phóng to ảnh đề bài"
              className="p-1 hover:text-apple-blue rounded text-gray-600 dark:text-gray-300"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Exit Button */}
          <button
            type="button"
            onClick={onExit}
            title="Thoát chế độ 2 cột (Esc)"
            className="px-2.5 py-1 text-xs font-bold bg-gray-200 dark:bg-gray-700/80 hover:bg-red-500 hover:text-white text-gray-700 dark:text-gray-200 rounded-lg transition flex items-center gap-1"
          >
            <X className="w-3.5 h-3.5" />
            <span>Thoát</span>
          </button>
        </div>
      </div>

      {/* 2 Independent Scrolling Columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* CỘT TRÁI: BÀI LÀM, SHEET ĐIỀN ĐÁP ÁN, TIMER, ĐỐI SOÁT */}
        <div
          style={{ width: `${splitRatio}%` }}
          className="h-full overflow-y-auto px-5 py-4 border-r border-gray-200 dark:border-gray-800 space-y-4"
        >
          <div className="pb-3 border-b border-gray-100 dark:border-gray-800">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              📝 Bàn Làm Bài & Ghi Nhận Đáp Án
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Điền câu trả lời trực tiếp bên dưới. Đề thi hiển thị độc lập ở cột bên phải.
            </p>
          </div>

          {/* Render markdown của bài làm */}
          <div className="text-xs sm:text-sm text-gray-800 dark:text-gray-200 leading-relaxed font-sans">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeRaw, rehypeKatex]}
              components={{
                // Audio override
                audio: ({ src }) => (src ? <CustomAudioPlayer src={src} /> : null),

                // Interactive IELTS Sheet & Writing cards
                div: ({ className, ...props }: any) => {
                  const cls = className || "";
                  if (cls.includes("ielts-sheet-card")) {
                    const sheetId = props["data-sheet-id"] || note.exam_metadata.sheet_id;
                    const startQ = parseInt(props["data-start-q"] || String(note.exam_metadata.start_q || 1), 10);
                    const endQ = parseInt(props["data-end-q"] || String(note.exam_metadata.end_q || 40), 10);
                    const timer = parseInt(props["data-timer"] || String(note.exam_metadata.timer_minutes || 20), 10);
                    const skill = note.exam_metadata.skill || (note.path.includes("reading") ? "reading" : "listening");

                    return (
                      <IeltsAnswerSheet
                        sheetId={sheetId}
                        startQ={startQ}
                        endQ={endQ}
                        initialMinutes={timer}
                        notePath={note.path}
                        skill={skill}
                        onSubmitted={onSubmitted}
                      />
                    );
                  }

                  if (cls.includes("ielts-writing-card")) {
                    const taskId = props["data-task"] || "task-1";
                    const target = parseInt(props["data-target"] || "150", 10);
                    const timer = parseInt(props["data-timer"] || "20", 10);

                    return (
                      <IeltsWritingWorkspace
                        taskId={taskId}
                        targetWords={target}
                        initialMinutes={timer}
                        notePath={note.path}
                        onSubmitted={onSubmitted}
                      />
                    );
                  }

                  if (cls.includes("ielts-ai-response") || cls.includes("ielts-grid-answers")) {
                    return null;
                  }

                  return <div className={cls} {...props} />;
                },

                blockquote: MarkdownBlockquote,
                ul: MarkdownUl,
                ol: MarkdownOl,
                li: MarkdownLi,
                code: MarkdownCode,

                // Table styling (macOS HIG & Quartz)
                table: MarkdownTable,
                thead: MarkdownThead,
                tbody: MarkdownTbody,
                tr: MarkdownTr,
                th: MarkdownTh,
                td: MarkdownTd,
              }}
            >
              {leftMarkdown}
            </ReactMarkdown>
          </div>
        </div>

        {/* CỘT PHẢI: ĐỀ BÀI, HÌNH ẢNH SÁCH GỐC, AUDIO SCRIPT */}
        <div
          style={{ width: `${100 - splitRatio}%` }}
          className="h-full overflow-y-auto px-4 py-4 bg-gray-50/50 dark:bg-[#12141a]/50 space-y-4 select-text"
        >
          {activeSection ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center gap-1.5 text-xs font-bold text-gray-800 dark:text-gray-200">
                  <BookOpen className="w-4 h-4 text-apple-blue" />
                  <span>{activeSection.summary}</span>
                </div>
                <span className="text-[11px] text-gray-400">Tỷ lệ zoom: {zoom}%</span>
              </div>

              {/* Nội dung đề bài & Hình ảnh được phóng to/thu nhỏ */}
              <div
                style={{ "--split-zoom": `${zoom}%` } as React.CSSProperties}
                className="split-images-wrapper space-y-0 text-xs sm:text-sm text-gray-800 dark:text-gray-200"
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeRaw, rehypeKatex]}
                  components={{
                    audio: ({ src }) => (src ? <CustomAudioPlayer src={src} /> : null),
                    p: ({ children }) => (
                      <p className="my-1 text-center leading-none">{children}</p>
                    ),
                    img: ({ src, alt }) => (
                      <img
                        src={src}
                        alt={alt || "Đề bài IELTS"}
                        style={{ maxWidth: `${zoom}%` }}
                        className="mx-auto rounded-lg shadow-sm border border-gray-200/60 dark:border-gray-700/60 my-1 object-contain transition-all"
                        loading="eager"
                      />
                    ),
                  }}
                >
                  {activeSection.body}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-xs text-gray-400">
              Không có tài liệu đề bài riêng cho bài này.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
