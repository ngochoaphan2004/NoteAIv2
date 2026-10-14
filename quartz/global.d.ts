/**
 * Global type declarations for Quartz inline scripts.
 *
 * These types augment the Window & globalThis interface for browser-side
 * scripts that are compiled separately by esbuild (*.inline.ts files).
 * They define globals injected at runtime by the SPA router and content pipeline.
 *
 * NOTE: This file uses `import type` inside `declare global {}` to stay as
 * a module-style file while still augmenting global scope.
 */

import type { ContentDetails } from "./plugins/emitters/contentIndex";
import type { FullSlug } from "./util/path";

declare global {
  // ---------------------------------------------------------------------------
  // Custom DOM Events
  // ---------------------------------------------------------------------------

  /**
   * Application-level custom events dispatched on `document`.
   */
  interface CustomEventMap {
    /** Fired by the SPA router after each navigation, carrying the new slug. */
    nav: CustomEvent<{ url: FullSlug }>;
    /** Fired by the SPA router just before navigation begins. */
    prenav: CustomEvent<Record<string, never>>;
    /** Fired by the dark-mode toggle when the active theme changes. */
    themechange: CustomEvent<{ theme: "light" | "dark" }>;
    /** Fired by the reader-mode toggle when the mode changes. */
    readermodechange: CustomEvent<{ mode: "on" | "off" }>;
  }

  // Override Document so addEventListener / dispatchEvent are typed.
  interface Document {
    addEventListener<K extends keyof CustomEventMap>(
      type: K,
      listener: (this: Document, ev: CustomEventMap[K]) => void,
      options?: boolean | AddEventListenerOptions,
    ): void;
    removeEventListener<K extends keyof CustomEventMap>(
      type: K,
      listener: (this: Document, ev: CustomEventMap[K]) => void,
      options?: boolean | EventListenerOptions,
    ): void;
    dispatchEvent<K extends keyof CustomEventMap>(
      ev: CustomEventMap[K],
    ): boolean;
  }

  // ---------------------------------------------------------------------------
  // Window globals injected by the SPA router (spa.inline.ts)
  // ---------------------------------------------------------------------------

  interface Window {
    /**
     * Registers a cleanup callback that will be called before each SPA
     * navigation (used to detach event listeners and tear down components).
     */
    addCleanup(fn: (...args: unknown[]) => void): void;

    /**
     * Triggers a SPA navigation to the given URL.
     * Injected by `spa.inline.ts` at runtime.
     */
    spaNavigate(url: URL, isBack?: boolean): Promise<void>;
  }

  // ---------------------------------------------------------------------------
  // Globals injected into inline scripts by the Quartz build pipeline
  // ---------------------------------------------------------------------------

  /**
   * The pre-fetched content index, available as a global `Promise` in
   * browser-side inline scripts. Resolved at runtime from `static/contentIndex.json`.
   */
  const fetchData: Promise<{ [slug: string]: ContentDetails }>;

  /**
   * Alias type used by search & graph inline scripts.
   * Maps a full slug string to its content metadata.
   */
  type ContentIndex = { [slug: string]: ContentDetails };
}

export {};
