import React, { useEffect, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeKatex from "rehype-katex";
import {
  FileText,
  Calendar,
  Tag,
  Columns,
} from "lucide-react";
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
import { CustomAudioPlayer } from "./CustomAudioPlayer";
import { StickyListeningAudioBar, extractAudioTracksFromMarkdown } from "./StickyListeningAudioBar";
import { IeltsAnswerSheet } from "./IeltsAnswerSheet";
import { IeltsWritingWorkspace } from "./IeltsWritingWorkspace";
import { pathToSlug, slugifyText } from "../../services/router";
import { NoteDetailResponse, EvaluationResponse } from "../../services/api";

interface NoteViewerProps {
  note: NoteDetailResponse;
  onNavigateNote: (path: string) => void;
  onSubmitted?: (result: EvaluationResponse) => void;
  onOpenSplitExam?: (sectionIndex?: number) => void;
}

export const NoteViewer: React.FC<NoteViewerProps> = ({
  note,
  onNavigateNote,
  onSubmitted,
  onOpenSplitExam,
}) => {
  // Pre-process markdown:
  // 1. Strip YAML Frontmatter (--- ... ---)
  let markdown = note.raw_content.replace(/^---\s*[\r\n]+[\s\S]*?[\r\n]+---\s*[\r\n]*/, "");

  // 2. Convert Wikilinks [[target|label]] and [[target]] to [label](target)
  markdown = markdown.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, target, label) => {
    const text = (label || target).trim();
    let link = target.trim();
    if (!link.endsWith(".md") && !link.includes("#")) {
      link = `${link}.md`;
    }
    return `[${text}](${link})`;
  });

  // Tự động cuộn tới anchor khi URL có #hash
  useEffect(() => {
    if (typeof window !== "undefined" && window.location.hash) {
      const targetId = window.location.hash.replace(/^#/, "");
      if (targetId) {
        setTimeout(() => {
          const el = document.getElementById(targetId);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }, 200);
      }
    }
  }, [note.path]);

  const generateHeadingId = (text: string) => {
    return slugifyText(text);
  };

  const audioTracks = useMemo(() => {
    return extractAudioTracksFromMarkdown(note.raw_content);
  }, [note.raw_content]);

  return (
    <article className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {audioTracks.length > 0 && (
        <StickyListeningAudioBar tracks={audioTracks} className="rounded-2xl shadow-sm mb-4" />
      )}
      {/* Frontmatter Header Title & Meta */}
      <header className="pb-4 border-b border-gray-200 dark:border-gray-800 space-y-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-gray-100 tracking-tight">
          {note.title}
        </h1>

        {note.frontmatter && (
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-gray-500 dark:text-gray-400">
            {note.frontmatter.tags && (
              <div className="flex items-center gap-1.5 flex-wrap">
                <Tag className="w-3.5 h-3.5 text-gray-400" />
                {(Array.isArray(note.frontmatter.tags)
                  ? note.frontmatter.tags
                  : [note.frontmatter.tags]
                ).map((tag: string, idx: number) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium text-[11px]"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {note.frontmatter["sr-due"] && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                <Calendar className="w-3 h-3" />
                Ôn tập: {note.frontmatter["sr-due"]}
              </span>
            )}
          </div>
        )}
      </header>

      {/* Main Markdown Body with Component Overrides */}
      <div className="max-w-none text-xs sm:text-sm leading-relaxed text-gray-800 dark:text-gray-200 font-sans">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeRaw, rehypeKatex]}
          components={{
            // Heading ID generation for TOC linking
            h1: ({ children }) => {
              const text = String(children || "");
              const id = generateHeadingId(text);
              return (
                <h1 id={id} className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-50 mt-8 mb-4 scroll-mt-20 border-b border-gray-200 dark:border-gray-800 pb-2">
                  {children}
                </h1>
              );
            },
            h2: ({ children }) => {
              const text = String(children || "");
              const id = generateHeadingId(text);
              return (
                <h2 id={id} className="text-lg sm:text-xl font-bold tracking-tight text-gray-900 dark:text-gray-100 mt-6 mb-3 scroll-mt-20 border-b border-gray-100 dark:border-gray-800/80 pb-1.5">
                  {children}
                </h2>
              );
            },
            h3: ({ children }) => {
              const text = String(children || "");
              const id = generateHeadingId(text);
              return (
                <h3 id={id} className="text-sm sm:text-base font-bold text-gray-800 dark:text-gray-200 mt-5 mb-2 scroll-mt-20">
                  {children}
                </h3>
              );
            },
            h4: ({ children }) => {
              const text = String(children || "");
              const id = generateHeadingId(text);
              return (
                <h4 id={id} className="text-xs font-bold uppercase tracking-wider text-apple-subtextLight dark:text-apple-subtextDark mt-4 mb-1.5 scroll-mt-20">
                  {children}
                </h4>
              );
            },

            // Paragraphs with macOS body text metrics
            p: ({ children }) => (
              <p className="text-[13.5px] sm:text-[14px] leading-[1.65] my-2.5 text-gray-800 dark:text-gray-200">
                {children}
              </p>
            ),

            // Lists
            ul: MarkdownUl,
            ol: MarkdownOl,
            li: MarkdownLi,

            // Typography formatting
            strong: ({ children }) => (
              <strong className="font-semibold text-gray-900 dark:text-gray-50">{children}</strong>
            ),
            em: ({ children }) => (
              <em className="italic text-gray-700 dark:text-gray-300">{children}</em>
            ),
            hr: () => (
              <hr className="my-6 border-gray-200 dark:border-gray-800" />
            ),

            // Inline and block code
            code: MarkdownCode,
            pre: ({ children }) => (
              <pre className="p-4 my-3 rounded-xl bg-gray-900 dark:bg-[#12141a] text-gray-100 text-xs font-mono overflow-x-auto border border-gray-800 shadow-sm leading-relaxed">
                {children}
              </pre>
            ),

            // Details and Summary with quick Split-Screen Exam Trigger
            details: ({ children, ...props }: any) => {
              return (
                <details
                  className="ielts-exam-details my-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/60 dark:bg-[#151821]/60 p-3 overflow-hidden shadow-sm transition"
                  {...props}
                >
                  {children}
                </details>
              );
            },
            summary: ({ children, ...props }: any) => {
              return (
                <summary
                  className="cursor-pointer font-bold text-xs sm:text-sm text-gray-800 dark:text-gray-100 flex items-center justify-between gap-2 p-1 hover:text-apple-blue transition select-none list-none [&::-webkit-details-marker]:hidden"
                  {...props}
                >
                  <span className="flex items-center gap-1.5">{children}</span>
                  {onOpenSplitExam && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onOpenSplitExam();
                      }}
                      title="Mở đề bài ở chế độ 2 cột độc lập (Alt+S)"
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-apple-blue/10 text-apple-blue hover:bg-apple-blue hover:text-white border border-apple-blue/30 transition flex items-center gap-1 flex-shrink-0 cursor-pointer shadow-sm"
                    >
                      <Columns className="w-3.5 h-3.5" />
                      <span>Xem 2 Cột</span>
                    </button>
                  )}
                </summary>
              );
            },

            // Audio Element override
            audio: ({ src, children, node, ...props }: any) => {
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
            },

            // Interactive IELTS Cards (Sheets & Writing)
            div: ({ node, className, ...props }: any) => {
              const cls = className || "";

              // Replace IELTS Sheet Card with native React component
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

              // Replace IELTS Writing Card with native React component
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

              // Ignore container div that used to hold old JS responses
              if (cls.includes("ielts-ai-response") || cls.includes("ielts-grid-answers")) {
                return null;
              }

              // Audio container box with nested audio
              if (cls.includes("ielts-audio-player-box")) {
                return <div className="my-2">{props.children}</div>;
              }

              return <div className={cls} {...props} />;
            },

            // Wikilink & Markdown Link Navigation
            a: ({ href, children, ...props }) => {
              if (!href) return <a {...props}>{children}</a>;

              // Check if internal document link
              const isExternal = href.startsWith("http://") || href.startsWith("https://");
              const isAnchor = href.startsWith("#");

              if (isExternal) {
                return (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-apple-blue hover:underline font-medium inline-flex items-center gap-0.5">
                    {children}
                  </a>
                );
              }

              if (isAnchor) {
                return (
                  <a href={href} className="text-apple-blue hover:underline">
                    {children}
                  </a>
                );
              }

              // Internal note navigation
              const handleInternalClick = (e: React.MouseEvent) => {
                e.preventDefault();
                let cleanPath = href.replace(/^\/+/, "");
                if (cleanPath.startsWith("content/")) {
                  cleanPath = cleanPath.slice("content/".length);
                }
                onNavigateNote(cleanPath);
              };

              const slugHref = pathToSlug(href);

              return (
                <a
                  href={slugHref}
                  onClick={handleInternalClick}
                  className="text-apple-blue hover:underline font-medium cursor-pointer"
                >
                  {children}
                </a>
              );
            },

            // Blockquote / GitHub Alert Callouts (Quartz style)
            blockquote: MarkdownBlockquote,

            // Table styling (macOS HIG & Quartz style)
            table: MarkdownTable,
            thead: MarkdownThead,
            tbody: MarkdownTbody,
            tr: MarkdownTr,
            th: MarkdownTh,
            td: MarkdownTd,
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>
    </article>
  );
};
