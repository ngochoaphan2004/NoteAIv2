// @ts-ignore
import splitExamScript from "./scripts/splitexam.inline";
import styles from "./styles/splitexam.scss";
import {
  QuartzComponent,
  QuartzComponentConstructor,
  QuartzComponentProps,
} from "./types";
import { classNames } from "../util/lang";

const SplitExamMode: QuartzComponent = ({
  displayClass,
}: QuartzComponentProps) => {
  return (
    <button
      type="button"
      class={classNames(displayClass, "splitexammode")}
      title="Chế độ thi 2 cột (Split Exam Mode - Alt+S)"
      aria-label="Split Exam Mode"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <title>Chế độ thi chia 2 cột độc lập (Alt+S)</title>
        <rect x="3" y="4" width="18" height="16" rx="2.5" ry="2.5" />
        <line x1="12" y1="4" x2="12" y2="20" stroke-dasharray="1 1" />
      </svg>
    </button>
  );
};

SplitExamMode.beforeDOMLoaded = splitExamScript;
SplitExamMode.css = styles;

export default (() => SplitExamMode) satisfies QuartzComponentConstructor;

