import React from "react";
import {
  Info,
  Lightbulb,
  AlertTriangle,
  AlertOctagon,
  Flame,
  CheckCircle2,
  HelpCircle,
  Sparkles,
  Quote,
  XCircle,
  Check,
  X,
} from "lucide-react";

export interface CalloutConfig {
  border: string;
  leftBar: string;
  bg: string;
  titleColor: string;
  defaultTitle: string;
  icon: React.ReactNode;
}

export const CALLOUT_CONFIGS: Record<string, CalloutConfig> = {
  note: {
    border: "border-blue-200/80 dark:border-blue-900/60",
    leftBar: "border-l-4 border-l-blue-500",
    bg: "bg-blue-50/70 dark:bg-blue-950/25",
    titleColor: "text-blue-700 dark:text-blue-300",
    defaultTitle: "GHI CHÚ",
    icon: <Info className="w-4 h-4 text-blue-500 shrink-0" />,
  },
  info: {
    border: "border-cyan-200/80 dark:border-cyan-900/60",
    leftBar: "border-l-4 border-l-cyan-500",
    bg: "bg-cyan-50/70 dark:bg-cyan-950/25",
    titleColor: "text-cyan-700 dark:text-cyan-300",
    defaultTitle: "THÔNG TIN",
    icon: <Info className="w-4 h-4 text-cyan-500 shrink-0" />,
  },
  tip: {
    border: "border-emerald-200/80 dark:border-emerald-900/60",
    leftBar: "border-l-4 border-l-emerald-500",
    bg: "bg-emerald-50/70 dark:bg-emerald-950/25",
    titleColor: "text-emerald-800 dark:text-emerald-300",
    defaultTitle: "MẸO HỌC & ĐỐI SOÁT",
    icon: <Lightbulb className="w-4 h-4 text-emerald-500 shrink-0" />,
  },
  success: {
    border: "border-green-200/80 dark:border-green-900/60",
    leftBar: "border-l-4 border-l-green-500",
    bg: "bg-green-50/70 dark:bg-green-950/25",
    titleColor: "text-green-700 dark:text-green-300",
    defaultTitle: "THÀNH CÔNG",
    icon: <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />,
  },
  important: {
    border: "border-purple-200/80 dark:border-purple-900/60",
    leftBar: "border-l-4 border-l-purple-500",
    bg: "bg-purple-50/70 dark:bg-purple-950/25",
    titleColor: "text-purple-700 dark:text-purple-300",
    defaultTitle: "QUAN TRỌNG",
    icon: <Flame className="w-4 h-4 text-purple-500 shrink-0" />,
  },
  warning: {
    border: "border-amber-200/80 dark:border-amber-900/60",
    leftBar: "border-l-4 border-l-amber-500",
    bg: "bg-amber-50/70 dark:bg-amber-950/25",
    titleColor: "text-amber-800 dark:text-amber-300",
    defaultTitle: "CẢNH BÁO",
    icon: <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />,
  },
  caution: {
    border: "border-rose-200/80 dark:border-rose-900/60",
    leftBar: "border-l-4 border-l-rose-500",
    bg: "bg-rose-50/70 dark:bg-rose-950/25",
    titleColor: "text-rose-700 dark:text-rose-300",
    defaultTitle: "CHÚ Ý LỖI SAI",
    icon: <AlertOctagon className="w-4 h-4 text-rose-500 shrink-0" />,
  },
  danger: {
    border: "border-red-200/80 dark:border-red-900/60",
    leftBar: "border-l-4 border-l-red-500",
    bg: "bg-red-50/70 dark:bg-red-950/25",
    titleColor: "text-red-700 dark:text-red-300",
    defaultTitle: "NGUY HIỂM",
    icon: <AlertOctagon className="w-4 h-4 text-red-500 shrink-0" />,
  },
  failure: {
    border: "border-rose-200/80 dark:border-rose-900/60",
    leftBar: "border-l-4 border-l-rose-500",
    bg: "bg-rose-50/70 dark:bg-rose-950/25",
    titleColor: "text-rose-700 dark:text-rose-300",
    defaultTitle: "THẤT BẠI",
    icon: <XCircle className="w-4 h-4 text-rose-500 shrink-0" />,
  },
  question: {
    border: "border-yellow-200/80 dark:border-yellow-900/60",
    leftBar: "border-l-4 border-l-yellow-500",
    bg: "bg-yellow-50/70 dark:bg-yellow-950/25",
    titleColor: "text-yellow-800 dark:text-yellow-300",
    defaultTitle: "CÂU HỎI",
    icon: <HelpCircle className="w-4 h-4 text-yellow-600 shrink-0" />,
  },
  example: {
    border: "border-indigo-200/80 dark:border-indigo-900/60",
    leftBar: "border-l-4 border-l-indigo-500",
    bg: "bg-indigo-50/70 dark:bg-indigo-950/25",
    titleColor: "text-indigo-700 dark:text-indigo-300",
    defaultTitle: "VÍ DỤ MINH HỌA",
    icon: <Sparkles className="w-4 h-4 text-indigo-500 shrink-0" />,
  },
  quote: {
    border: "border-gray-200 dark:border-gray-700",
    leftBar: "border-l-4 border-l-gray-400",
    bg: "bg-gray-50/70 dark:bg-gray-900/30",
    titleColor: "text-gray-700 dark:text-gray-300",
    defaultTitle: "TRÍCH DẪN",
    icon: <Quote className="w-4 h-4 text-gray-400 shrink-0" />,
  },
};

/**
 * Trích xuất loại callout, tiêu đề và thân bài từ các con của blockquote
 */
export function parseCallout(children: React.ReactNode) {
  const childArray = React.Children.toArray(children).filter(
    (c) => !(typeof c === "string" && c.trim() === "")
  );
  if (childArray.length === 0) return null;

  const firstChild = childArray[0] as any;
  if (!firstChild || !firstChild.props) return null;

  const pChildren = React.Children.toArray(firstChild.props.children);
  if (pChildren.length === 0) return null;

  const firstText = typeof pChildren[0] === "string" ? pChildren[0] : "";
  const match = firstText.match(/^\[!([a-zA-Z0-9_-]+)\][ \t]*(.*)/);
  if (!match) return null;

  const rawType = match[1].toLowerCase();
  const restOfFirstLine = match[2];

  const config =
    CALLOUT_CONFIGS[rawType] ||
    (rawType === "todo" ? CALLOUT_CONFIGS.info : CALLOUT_CONFIGS.note);

  // Tách tiêu đề tùy biến và phần nội dung còn lại của đoạn văn đầu tiên
  let titleParts: React.ReactNode[] = [];
  let bodyInFirstP: React.ReactNode[] = [];
  let isTitle = true;

  if (restOfFirstLine) {
    const parts = restOfFirstLine.split("\n");
    if (parts[0].trim()) {
      titleParts.push(parts[0].trim());
    }
    if (parts.length > 1) {
      isTitle = false;
      const rem = parts.slice(1).join("\n").trim();
      if (rem) bodyInFirstP.push(rem);
    }
  }

  for (let i = 1; i < pChildren.length; i++) {
    const item = pChildren[i];
    if (isTitle) {
      if (typeof item === "string") {
        const parts = item.split("\n");
        if (parts[0].trim()) titleParts.push(parts[0]);
        if (parts.length > 1) {
          isTitle = false;
          const rem = parts.slice(1).join("\n").trim();
          if (rem) bodyInFirstP.push(rem);
        }
      } else {
        titleParts.push(item);
      }
    } else {
      bodyInFirstP.push(item);
    }
  }

  const remainingChildren = childArray.slice(1);
  let newBody: React.ReactNode[] = [];
  if (bodyInFirstP.length > 0) {
    newBody.push(
      React.cloneElement(
        firstChild,
        {
          key: "callout-p0",
          className:
            "my-1.5 leading-relaxed text-gray-800 dark:text-gray-200",
        },
        ...bodyInFirstP
      )
    );
  }
  newBody = newBody.concat(remainingChildren);

  const finalTitle =
    titleParts.length > 0 ? titleParts : [config.defaultTitle];

  return {
    config,
    title: finalTitle,
    body: newBody,
  };
}

/**
 * Render Callout hoặc Blockquote theo phong cách Quartz
 */
export const MarkdownBlockquote: React.FC<{ children?: React.ReactNode }> = ({
  children,
}) => {
  const callout = parseCallout(children);

  if (callout) {
    const { config, title, body } = callout;
    return (
      <div
        className={`callout my-4 rounded-xl border ${config.border} ${config.leftBar} ${config.bg} p-3.5 sm:p-4.5 shadow-xs transition-all`}
      >
        <div
          className={`callout-title flex items-center gap-2 font-bold text-xs sm:text-sm ${config.titleColor} select-none`}
        >
          {config.icon}
          <div className="callout-title-inner flex items-center gap-1.5 flex-wrap">
            {title}
          </div>
        </div>
        {body && body.length > 0 && (
          <div className="callout-content mt-2 text-xs sm:text-sm text-gray-800 dark:text-gray-200 leading-relaxed space-y-1.5">
            {body}
          </div>
        )}
      </div>
    );
  }

  return (
    <blockquote className="my-4 pl-4 py-1 border-l-[3px] border-apple-blue/70 bg-gray-50/50 dark:bg-gray-800/20 rounded-r-lg text-gray-700 dark:text-gray-300 text-xs sm:text-sm leading-relaxed not-italic">
      {children}
    </blockquote>
  );
};

/**
 * Xử lý nội dung ô bảng (td) với badge kết quả, câu hỏi, và định dạng sắc nét
 */
export function enhanceTableCellContent(children: React.ReactNode) {
  const childArray = React.Children.toArray(children);
  if (childArray.length === 0) return children;

  // Nếu ô chỉ có 1 chuỗi ký tự đơn giản
  if (childArray.length === 1 && typeof childArray[0] === "string") {
    const trimmed = childArray[0].trim();

    if (trimmed === "❌") {
      return (
        <span className="inline-flex items-center justify-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/70 dark:text-rose-300 border border-rose-200/80 dark:border-rose-900/60 shadow-2xs whitespace-nowrap select-none">
          <X className="w-3.5 h-3.5 text-rose-500 shrink-0" />
          <span>Sai</span>
        </span>
      );
    }

    if (trimmed === "✅") {
      return (
        <span className="inline-flex items-center justify-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/70 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-900/60 shadow-2xs whitespace-nowrap select-none">
          <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
          <span>Đúng</span>
        </span>
      );
    }

    if (trimmed === "⚪" || trimmed === "[ ]") {
      return (
        <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400 border border-gray-200 dark:border-gray-700 whitespace-nowrap select-none">
          Bỏ trống
        </span>
      );
    }

    if (trimmed === "[x]") {
      return (
        <span className="inline-flex items-center justify-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300 border border-blue-200/80 dark:border-blue-900/60 shadow-2xs whitespace-nowrap select-none">
          <Check className="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span>Đã làm</span>
        </span>
      );
    }

    // Tiền tố phân tích dạng bài / bẫy
    const tagMatch = trimmed.match(
      /^(Gap-fill|Multiple choice|Matching|Sentence completion|Diagram labelling|Bẫy|Trap|Dẫn chứng):\s*(.*)/i
    );
    if (tagMatch) {
      return (
        <span className="inline">
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold bg-blue-50/90 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200/70 dark:border-blue-900/60 mr-1.5 shadow-2xs select-none">
            {tagMatch[1]}
          </span>
          <span className="text-gray-700 dark:text-gray-300 leading-relaxed">
            {tagMatch[2]}
          </span>
        </span>
      );
    }
  }

  return children;
}

/**
 * Render Header bảng (th) với độ rộng cố định và không bị ngắt dòng khó coi
 */
export const MarkdownTh: React.FC<any> = ({ children, style, ...props }) => {
  const text = String(
    React.Children.toArray(children)
      .map((c: any) => (typeof c === "string" ? c : c?.props?.children || ""))
      .join("")
  )
    .trim()
    .toLowerCase();

  let alignmentClass = "text-left";
  let widthClass = "min-w-[120px]";

  if (text === "stt" || text === "#" || text === "câu" || text === "no.") {
    alignmentClass = "text-center";
    widthClass = "w-14 min-w-[56px] whitespace-nowrap";
  } else if (
    text.includes("bài làm") ||
    text.includes("bạn đã chọn") ||
    text.includes("your answer")
  ) {
    alignmentClass = "text-center";
    widthClass = "min-w-[130px] whitespace-nowrap";
  } else if (
    text.includes("đáp án") ||
    text.includes("chuẩn") ||
    text.includes("correct")
  ) {
    alignmentClass = "text-center";
    widthClass = "min-w-[140px] whitespace-nowrap";
  } else if (
    text.includes("kết quả") ||
    text.includes("trạng thái") ||
    text.includes("status") ||
    text.includes("result")
  ) {
    alignmentClass = "text-center";
    widthClass = "min-w-[95px] whitespace-nowrap";
  } else if (
    text.includes("ghi chú") ||
    text.includes("phân tích") ||
    text.includes("giải thích") ||
    text.includes("lỗi sai") ||
    text.includes("bẫy") ||
    text.includes("explanation")
  ) {
    alignmentClass = "text-left";
    widthClass = "min-w-[320px]";
  } else if (style?.textAlign === "center") {
    alignmentClass = "text-center";
    widthClass = "whitespace-nowrap";
  }

  return (
    <th
      className={`py-3 px-3.5 text-xs font-bold tracking-tight select-none ${alignmentClass} ${widthClass}`}
      style={style}
      {...props}
    >
      {children}
    </th>
  );
};

/**
 * Render Ô dữ liệu (td) với căn lề thông minh
 */
export const MarkdownTd: React.FC<any> = ({ children, style, ...props }) => {
  const enhanced = enhanceTableCellContent(children);

  let isCenter = style?.textAlign === "center";
  const childArray = React.Children.toArray(children);

  // Tự động căn giữa số thứ tự, ký hiệu đáp án ngắn hoặc huy hiệu
  if (childArray.length === 1) {
    const item: any = childArray[0];
    if (typeof item === "string") {
      const trimmed = item.trim();
      if (
        /^\d+$/.test(trimmed) ||
        trimmed === "❌" ||
        trimmed === "✅" ||
        trimmed === "⚪" ||
        trimmed === "[ ]" ||
        trimmed === "[x]" ||
        /^[A-Ga-g]$/.test(trimmed)
      ) {
        isCenter = true;
      }
    } else if (item?.type === "strong" && typeof item?.props?.children === "string") {
      const trimmed = item.props.children.trim();
      if (/^\d+$/.test(trimmed)) {
        isCenter = true;
      }
    }
  }

  return (
    <td
      className={`py-3 px-3.5 text-xs sm:text-[13px] text-gray-800 dark:text-gray-200 leading-relaxed align-middle ${
        isCenter ? "text-center font-medium" : "text-left"
      }`}
      style={style}
      {...props}
    >
      {enhanced}
    </td>
  );
};

/**
 * Container Bảng Responsive chuẩn Quartz
 */
export const MarkdownTable: React.FC<any> = ({ children, ...props }) => (
  <div className="table-container my-5 overflow-hidden rounded-xl border border-gray-200/90 dark:border-gray-800/90 shadow-xs bg-white dark:bg-[#151720]">
    <div className="overflow-x-auto">
      <table
        className="min-w-full divide-y divide-gray-200 dark:divide-gray-800 border-collapse text-left font-sans text-xs sm:text-[13px]"
        {...props}
      >
        {children}
      </table>
    </div>
  </div>
);

export const MarkdownThead: React.FC<any> = ({ children, ...props }) => (
  <thead
    className="bg-gray-50/90 dark:bg-[#1a1d27] border-b border-gray-200 dark:border-gray-800 font-bold text-gray-700 dark:text-gray-200 uppercase tracking-wider text-[11px]"
    {...props}
  >
    {children}
  </thead>
);

export const MarkdownTbody: React.FC<any> = ({ children, ...props }) => (
  <tbody
    className="divide-y divide-gray-100 dark:divide-gray-800/60 bg-white dark:bg-[#151720]"
    {...props}
  >
    {children}
  </tbody>
);

export const MarkdownTr: React.FC<any> = ({ children, ...props }) => (
  <tr
    className="border-b border-gray-100 dark:border-gray-800/60 hover:bg-gray-50/80 dark:hover:bg-gray-800/35 transition-colors"
    {...props}
  >
    {children}
  </tr>
);

/**
 * Inline & Block Code chuẩn Quartz
 */
export const MarkdownCode: React.FC<any> = ({
  inline,
  className,
  children,
  ...props
}) => {
  if (inline || !className) {
    return (
      <code className="px-1.5 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800/90 text-blue-700 dark:text-blue-300 font-mono text-[12px] font-semibold border border-gray-200/80 dark:border-gray-700/70 tracking-tight">
        {children}
      </code>
    );
  }
  return (
    <code className={`${className} font-mono text-xs`} {...props}>
      {children}
    </code>
  );
};

/**
 * Lists chuẩn Quartz
 */
export const MarkdownUl: React.FC<any> = ({ children, ...props }) => (
  <ul
    className="list-disc list-outside pl-5 space-y-1.5 my-2.5 text-[13.5px] sm:text-[14px] leading-relaxed text-gray-800 dark:text-gray-200 marker:text-gray-400 dark:marker:text-gray-500"
    {...props}
  >
    {children}
  </ul>
);

export const MarkdownOl: React.FC<any> = ({ children, ...props }) => (
  <ol
    className="list-decimal list-outside pl-5 space-y-1.5 my-2.5 text-[13.5px] sm:text-[14px] leading-relaxed text-gray-800 dark:text-gray-200 marker:text-gray-500 font-medium"
    {...props}
  >
    {children}
  </ol>
);

export const MarkdownLi: React.FC<any> = ({ children, ...props }) => (
  <li className="leading-relaxed pl-1" {...props}>
    {children}
  </li>
);
