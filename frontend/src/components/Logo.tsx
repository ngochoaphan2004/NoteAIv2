import React from "react";

interface LogoProps {
  size?: number;
  className?: string;
  showText?: boolean;
}

export const LogoSvg: React.FC<{ size?: number; className?: string }> = ({
  size = 32,
  className = "",
}) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 120 120"
    width={size}
    height={size}
    fill="none"
    className={`select-none flex-shrink-0 transition-transform duration-300 hover:scale-105 ${className}`}
  >
    <defs>
      <linearGradient id="noteai-brand-bg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#0071E3" />
        <stop offset="45%" stopColor="#2563EB" />
        <stop offset="100%" stopColor="#4F46E5" />
      </linearGradient>

      <linearGradient id="noteai-brand-glass" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.32" />
        <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.0" />
      </linearGradient>

      <linearGradient id="noteai-brand-spark" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#38BDF8" />
        <stop offset="50%" stopColor="#FACC15" />
        <stop offset="100%" stopColor="#FB7185" />
      </linearGradient>

      <filter id="noteai-brand-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="3" stdDeviation="3.5" floodColor="#0F172A" floodOpacity="0.3" />
      </filter>
    </defs>

    <rect width="120" height="120" rx="28" fill="url(#noteai-brand-bg)" />
    <rect width="120" height="120" rx="28" fill="url(#noteai-brand-glass)" stroke="rgba(255,255,255,0.25)" strokeWidth="1.5" />

    <g filter="url(#noteai-brand-shadow)">
      <path d="M 26 36 C 26 31, 42 28, 56 33 L 56 83 C 42 78, 26 81, 26 86 Z" fill="#FFFFFF" fillOpacity="0.97" />
      <path d="M 64 33 C 78 28, 94 31, 94 36 L 94 86 C 94 81, 78 78, 64 83 Z" fill="#EEF2F6" fillOpacity="0.92" />
      <path d="M 56 33 L 64 33 L 64 83 L 56 83 Z" fill="#CBD5E1" fillOpacity="0.85" />
      <path d="M 32 46 Q 44 43 54 47 L 54 51 Q 44 47 32 50 Z" fill="#0071E3" fillOpacity="0.75" />
      <path d="M 66 47 Q 76 43 88 46 L 88 50 Q 76 47 66 51 Z" fill="#2563EB" fillOpacity="0.75" />
      <path d="M 32 59 Q 44 56 54 60 L 54 64 Q 44 60 32 63 Z" fill="#0071E3" fillOpacity="0.75" />
      <path d="M 66 60 Q 76 56 88 59 L 88 63 Q 76 60 66 64 Z" fill="#2563EB" fillOpacity="0.75" />

      <g transform="translate(86, 26)">
        <path d="M 0 -13 C 0 -4, 4 0, 13 0 C 4 0, 0 4, 0 13 C 0 4, -4 0, -13 0 C -4 0, 0 -4, 0 -13 Z" fill="url(#noteai-brand-spark)" />
        <circle cx="0" cy="0" r="2.5" fill="#FFFFFF" />
      </g>

      <g transform="translate(100, 42)">
        <path d="M 0 -6 C 0 -2, 2 0, 6 0 C 2 0, 0 2, 0 6 C 0 2, -2 0, -6 0 C -2 0, 0 -2, 0 -6 Z" fill="#FDE047" />
      </g>
    </g>
  </svg>
);

export const Logo: React.FC<LogoProps> = ({
  size = 32,
  className = "",
  showText = false,
}) => {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <LogoSvg size={size} />

      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-extrabold tracking-tight leading-none bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 dark:from-white dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent">
              NoteAI
            </span>
            <span className="text-[10px] font-black px-1.5 py-0.5 rounded-md bg-blue-100 dark:bg-blue-950/80 text-apple-blue dark:text-blue-400 border border-blue-200 dark:border-blue-800/60 leading-none">
              v2
            </span>
          </div>
          <span className="text-[9px] text-apple-subtextLight dark:text-apple-subtextDark uppercase tracking-wider font-semibold mt-0.5">
            Local Autonomous PKM
          </span>
        </div>
      )}
    </div>
  );
};

export default Logo;
