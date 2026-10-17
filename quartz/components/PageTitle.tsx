import { pathToRoot } from "../util/path";
import {
  QuartzComponent,
  QuartzComponentConstructor,
  QuartzComponentProps,
} from "./types";
import { classNames } from "../util/lang";
import { i18n } from "../i18n";

const PageTitle: QuartzComponent = ({
  fileData,
  cfg,
  displayClass,
}: QuartzComponentProps) => {
  const title = cfg?.pageTitle ?? i18n(cfg.locale).propertyDefaults.title;
  const baseDir = pathToRoot(fileData.slug!);
  return (
    <h2 class={classNames(displayClass, "page-title")}>
      <a href={baseDir} class="page-title-link">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 120 120"
          width="28"
          height="28"
          fill="none"
          class="page-title-logo"
        >
          <defs>
            <linearGradient id="quartz-logo-bg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#0071E3" />
              <stop offset="45%" stop-color="#2563EB" />
              <stop offset="100%" stop-color="#4F46E5" />
            </linearGradient>
            <linearGradient id="quartz-logo-glass" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.32" />
              <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0.0" />
            </linearGradient>
            <linearGradient id="quartz-spark-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#38BDF8" />
              <stop offset="50%" stop-color="#FACC15" />
              <stop offset="100%" stop-color="#FB7185" />
            </linearGradient>
          </defs>
          <rect width="120" height="120" rx="28" fill="url(#quartz-logo-bg)" />
          <rect width="120" height="120" rx="28" fill="url(#quartz-logo-glass)" stroke="rgba(255,255,255,0.25)" stroke-width="1.5" />
          <g>
            <path d="M 26 36 C 26 31, 42 28, 56 33 L 56 83 C 42 78, 26 81, 26 86 Z" fill="#FFFFFF" fill-opacity="0.97" />
            <path d="M 64 33 C 78 28, 94 31, 94 36 L 94 86 C 94 81, 78 78, 64 83 Z" fill="#EEF2F6" fill-opacity="0.92" />
            <path d="M 56 33 L 64 33 L 64 83 L 56 83 Z" fill="#CBD5E1" fill-opacity="0.85" />
            <path d="M 32 46 Q 44 43 54 47 L 54 51 Q 44 47 32 50 Z" fill="#0071E3" fill-opacity="0.75" />
            <path d="M 66 47 Q 76 43 88 46 L 88 50 Q 76 47 66 51 Z" fill="#2563EB" fill-opacity="0.75" />
            <path d="M 32 59 Q 44 56 54 60 L 54 64 Q 44 60 32 63 Z" fill="#0071E3" fill-opacity="0.75" />
            <path d="M 66 60 Q 76 56 88 59 L 88 63 Q 76 60 66 64 Z" fill="#2563EB" fill-opacity="0.75" />
            <g transform="translate(86, 26)">
              <path d="M 0 -13 C 0 -4, 4 0, 13 0 C 4 0, 0 4, 0 13 C 0 4, -4 0, -13 0 C -4 0, 0 -4, 0 -13 Z" fill="url(#quartz-spark-grad)" />
              <circle cx="0" cy="0" r="2.5" fill="#FFFFFF" />
            </g>
            <g transform="translate(100, 42)">
              <path d="M 0 -6 C 0 -2, 2 0, 6 0 C 2 0, 0 2, 0 6 C 0 2, -2 0, -6 0 C -2 0, 0 -2, 0 -6 Z" fill="#FDE047" />
            </g>
          </g>
        </svg>
        <span>{title}</span>
      </a>
    </h2>
  );
};

PageTitle.css = `
.page-title {
  font-size: 1.5rem;
  margin: 0;
  font-family: var(--titleFont);
}

.page-title-link {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  text-decoration: none;
  color: var(--dark);
}

.page-title-logo {
  border-radius: 7px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-title-link:hover .page-title-logo {
  transform: scale(1.1) rotate(-2deg);
}
`;

export default (() => PageTitle) satisfies QuartzComponentConstructor;
