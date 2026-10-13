// @ts-ignore
import interactiveScript from "./scripts/interactive.inline"
import interactiveStyles from "./styles/interactive.scss"
import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"

const Interactive: QuartzComponent = (_props: QuartzComponentProps) => {
  return null
}

Interactive.afterDOMLoaded = interactiveScript
Interactive.css = interactiveStyles

export default (() => Interactive) satisfies QuartzComponentConstructor
