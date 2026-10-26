import React, { useState, useEffect, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeKatex from "rehype-katex";
import {
  Columns,
  ZoomIn,
  ZoomOut,
  X,
  BookOpen,
  ArrowLeftRight,
  Maximize2,
  Minimize2,
  RotateCcw,
  CheckCircle2,
  FileText,
  Clock,
} from "lucide-react";
import { IeltsAnswerSheet } from "./IeltsAnswerSheet";
import { IeltsWritingWorkspace } from "./IeltsWritingWorkspace";
import { CustomAudioPlayer } from "./CustomAudioPlayer";
import {
  StickyListeningAudioBar,
  extractAudioTracksFromMarkdown,
  AudioTrack,
} from "./StickyListeningAudioBar";
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
  const [zoom, setZoom] = useState(100); // 50% to 200%
  const [splitRatio, setSplitRatio] = useState<50 | 40 | 60>(50); // Left column width %
  const [isSwapped, setIsSwapped] = useState(false); // false: Left = Đề bài, Right = Bài làm
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Trích xuất audio tracks cho bài Listening
  const audioTracks = useMemo<AudioTrack[]>(() => {
    return extractAudioTracksFromMarkdown(note.raw_content);
  }, [note.raw_content]);

  // Trích xuất các khối <details> chứa đề thi/ảnh và nội dung bài làm
  const { sections, workspaceMarkdown } = useMemo(() => {
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

    let cleanWorkspace = raw;

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

      // Xóa sạch khối <details> khỏi cột bài làm để giao diện thoáng, không bị chèn quote rác
      cleanWorkspace = cleanWorkspace.replace(full, "");
    }

    return { sections: extracted, workspaceMarkdown: cleanWorkspace.trim() };
  }, [note.raw_content]);

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

  // Helper render audio component trong markdown
  const renderAudioComponent = ({ src, children, node, ...props }: any) => {
    let audioSrc = src;
    if (!audioSrc && node?.children) {
      const sourceEl = node.children.find((c: any) => c.tagName === "source" && c.properties?.src);
      if (sourceEl) audioSrc = sourceEl.properties.src;
    }
    if (!audioSrc && children) {
      React.Children.forEach(children, (child: any) => {
        if (child?.props?.src) audioSrc = child.props.src;
      });
    }
    if (audioSrc) {
      return <CustomAudioPlayer src={audioSrc} />;
    }
    return <audio controls className="w-full my-2" {...props}>{children}</audio>;
  };

  // Cột Đề Bài (Passage & Original Images)
  const renderExamDocPane = () => (
    <div className="h-full flex flex-col overflow-hidden bg-gray-50/70 dark:bg-[#12151d]/70">
      {/* Sub-header của Pane Đề Thi */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-white/80 dark:bg-[#181b24]/80 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <BookOpen className="w-4 h-4 text-apple-blue flex-shrink-0" />
          <span className="text-xs font-bold text-gray-800 dark:text-gray-100 truncate">
            {activeSection?.summary || "Tài Liệu Đề Thi & Bài Đọc"}
          </span>
        </div>

        {/* Zoom Controls Bar */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(50, z - 15))}
            title="Thu nhỏ ảnh (-15%)"
            className="p-1 rounded-md text-gray-600 dark:text-gray-300 hover:text-apple-blue hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setZoom(100)}
            title="Nhấp để đặt lại kích thước chuẩn (100%)"
            className="px-2 py-0.5 text-[11px] font-mono font-bold text-gray-700 dark:text-gray-300 hover:text-apple-blue bg-gray-100 dark:bg-gray-800 rounded transition"
          >
            {zoom}%
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(200, z + 15))}
            title="Phóng to ảnh (+15%)"
            className="p-1 rounded-md text-gray-600 dark:text-gray-300 hover:text-apple-blue hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Nội dung đề bài & Hình ảnh cuộn độc lập */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-4 select-text">
        {activeSection ? (
          <div className="space-y-4 max-w-3xl mx-auto">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeRaw, rehypeKatex]}
              components={{
                audio: renderAudioComponent,
                p: ({ children }) => (
                  <p className="my-2.5 text-[13.5px] sm:text-[14px] leading-relaxed text-gray-800 dark:text-gray-200">
                    {children}
                  </p>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mt-4 mb-2 pb-1 border-b border-gray-200/60 dark:border-gray-800">
                    {children}
                  </h3>
                ),
                h4: ({ children }) => (
                  <h4 className="text-xs font-bold uppercase tracking-wider text-apple-blue mt-3 mb-1">
                    {children}
                  </h4>
                ),
                img: ({ src, alt }) => (
                  <div className="my-3 text-center">
                    <img
                      src={src}
                      alt={alt || "Đề bài IELTS"}
                      style={{
                        width: `${zoom}%`,
                        maxWidth: zoom <= 100 ? "100%" : "none",
                        height: "auto",
                      }}
                      className="mx-auto rounded-xl shadow-md border border-gray-200/80 dark:border-gray-700/80 object-contain block transition-all duration-150"
                      loading="eager"
                    />
                    {alt && (
                      <span className="block mt-1 text-[11px] text-gray-400 font-medium">
                        {alt}
                      </span>
                    )}
                  </div>
                ),
                blockquote: MarkdownBlockquote,
                table: MarkdownTable,
                thead: MarkdownThead,
                tbody: MarkdownTbody,
                tr: MarkdownTr,
                th: MarkdownTh,
                td: MarkdownTd,
                ul: MarkdownUl,
                ol: MarkdownOl,
                li: MarkdownLi,
                code: MarkdownCode,
              }}
            >
              {activeSection.body}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="py-20 text-center text-xs text-gray-400">
            Không có tài liệu đề bài riêng cho bài này. Bạn có thể làm bài trực tiếp ở cột bên cạnh.
          </div>
        )}
      </div>
    </div>
  );

  // Cột Bài Làm (Interactive Answer Sheet & Workspace)
  const renderWorkspacePane = () => (
    <div className="h-full flex flex-col overflow-hidden bg-white dark:bg-[#1a1d26]">
      {/* Sub-header của Pane Bài Làm */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-gray-50/80 dark:bg-[#181b24]/80 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-apple-blue" />
          <span className="text-xs font-bold text-gray-800 dark:text-gray-100">
            📝 Phiếu Trả Lời & Bàn Làm Bài
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-gray-500 font-medium">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>Tự động đối soát chuẩn Cambridge</span>
        </div>
      </div>

      {/* Nội dung bài làm cuộn độc lập */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-5 py-4 space-y-4">
        <div className="text-xs sm:text-sm text-gray-800 dark:text-gray-200 leading-relaxed font-sans max-w-2xl mx-auto">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeRaw, rehypeKatex]}
            components={{
              audio: renderAudioComponent,

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
              table: MarkdownTable,
              thead: MarkdownThead,
              tbody: MarkdownTbody,
              tr: MarkdownTr,
              th: MarkdownTh,
              td: MarkdownTd,
            }}
          >
            {workspaceMarkdown}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );

  return (
    <div
      className={`w-full flex flex-col bg-white dark:bg-[#1a1d26] rounded-2xl border border-gray-200 dark:border-gray-800 shadow-xl overflow-hidden select-text animate-fadeIn transition-all duration-200 ${
        isFullscreen
          ? "fixed inset-0 z-50 rounded-none h-screen"
          : "h-[calc(100vh-120px)] min-h-[620px]"
      }`}
    >
      {/* 1. Exam Split Topbar (Apple HIG Glassmorphism) */}
      <div className="flex flex-wrap items-center justify-between px-3.5 py-2 bg-white/90 dark:bg-[#151822]/90 border-b border-gray-200 dark:border-gray-800 backdrop-blur-md gap-2 flex-shrink-0 z-10">
        {/* Left Side: Mode badge and note title */}
        <div className="flex items-center gap-2 min-w-0">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-apple-blue text-white shadow-xs flex-shrink-0">
            <Columns className="w-3.5 h-3.5" />
            <span>Phòng Thi 2 Cột</span>
          </span>
          <span className="text-xs font-bold text-gray-800 dark:text-gray-200 truncate max-w-[200px] sm:max-w-xs">
            {note.title}
          </span>
        </div>

        {/* Center: Section Switcher Tabs (Part 1, Part 2, Passage...) */}
        {sections.length > 1 && (
          <div className="flex items-center bg-gray-100 dark:bg-gray-800 p-0.5 rounded-lg border border-gray-200 dark:border-gray-700">
            {sections.map((sec, idx) => (
              <button
                key={sec.id}
                type="button"
                onClick={() => setActiveSectionIdx(idx)}
                className={`px-3 py-1 text-xs font-bold rounded-md transition ${
                  idx === activeSectionIdx
                    ? "bg-white dark:bg-[#1e2330] text-apple-blue shadow-xs"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                }`}
              >
                {sec.summary.replace(/^(📄|📜|🎧|📖)\s*/, "").slice(0, 30)}
              </button>
            ))}
          </div>
        )}

        {/* Right Side: Split Ratio, Swap Columns, Fullscreen & Exit */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {/* Swap Columns (⇄ Đổi bên) */}
          <button
            type="button"
            onClick={() => setIsSwapped(!isSwapped)}
            title="Đổi bên hiển thị (Đề bài ⇄ Phiếu trả lời)"
            className={`p-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1 transition ${
              isSwapped
                ? "bg-blue-50 dark:bg-blue-950/40 text-apple-blue border-blue-200 dark:border-blue-800"
                : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:text-apple-blue"
            }`}
          >
            <ArrowLeftRight className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Đổi bên</span>
          </button>

          {/* Split Ratio Presets */}
          <div className="hidden sm:flex items-center bg-gray-100 dark:bg-gray-800 p-0.5 rounded-lg border border-gray-200 dark:border-gray-700 text-xs font-semibold">
            <button
              type="button"
              onClick={() => setSplitRatio(50)}
              title="Chia đều 50:50"
              className={`px-2 py-0.5 rounded transition ${
                splitRatio === 50
                  ? "bg-white dark:bg-[#1e2330] text-apple-blue shadow-xs font-bold"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-800"
              }`}
            >
              50:50
            </button>
            <button
              type="button"
              onClick={() => setSplitRatio(60)}
              title="Cột 1: 60% - Cột 2: 40%"
              className={`px-2 py-0.5 rounded transition ${
                splitRatio === 60
                  ? "bg-white dark:bg-[#1e2330] text-apple-blue shadow-xs font-bold"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-800"
              }`}
            >
              60:40
            </button>
            <button
              type="button"
              onClick={() => setSplitRatio(40)}
              title="Cột 1: 40% - Cột 2: 60%"
              className={`px-2 py-0.5 rounded transition ${
                splitRatio === 40
                  ? "bg-white dark:bg-[#1e2330] text-apple-blue shadow-xs font-bold"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-800"
              }`}
            >
              40:60
            </button>
          </div>

          {/* Fullscreen Toggle */}
          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? "Thu nhỏ lại (Cửa sổ)" : "Toàn màn hình (Tập trung làm bài)"}
            className="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:text-apple-blue text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 transition"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>

          {/* Exit Button */}
          <button
            type="button"
            onClick={onExit}
            title="Thoát chế độ 2 cột (Esc)"
            className="px-2.5 py-1 text-xs font-bold bg-gray-100 dark:bg-gray-800 hover:bg-rose-500 hover:text-white text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg transition flex items-center gap-1"
          >
            <X className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Thoát</span>
          </button>
        </div>
      </div>

      {/* 2. Global Audio Controller Bar (Chuyên phục vụ các bài thi Listening) */}
      {audioTracks.length > 0 && (
        <StickyListeningAudioBar
          tracks={audioTracks}
          currentTrackIdx={Math.min(activeSectionIdx, audioTracks.length - 1)}
          onTrackChange={(idx) => {
            if (idx < sections.length) {
              setActiveSectionIdx(idx);
            }
          }}
        />
      )}

      {/* 3. Two Independent Scrolling Columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* Pane 1 (Mặc định: Trái = Đề bài, nếu swapped: Trái = Bài làm) */}
        <div
          style={{ width: `${splitRatio}%` }}
          className="h-full border-r border-gray-200 dark:border-gray-800 overflow-hidden"
        >
          {isSwapped ? renderWorkspacePane() : renderExamDocPane()}
        </div>

        {/* Pane 2 (Mặc định: Phải = Bài làm, nếu swapped: Phải = Đề bài) */}
        <div
          style={{ width: `${100 - splitRatio}%` }}
          className="h-full overflow-hidden"
        >
          {isSwapped ? renderExamDocPane() : renderWorkspacePane()}
        </div>
      </div>
    </div>
  );
};
