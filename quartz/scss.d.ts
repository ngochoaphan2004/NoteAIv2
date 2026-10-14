/**
 * TypeScript module declarations for SCSS files.
 *
 * Quartz uses esbuild-sass-plugin to process SCSS at build time.
 * This declaration tells tsc to treat any `*.scss` import as a plain
 * string (the compiled CSS text), matching what esbuild actually returns.
 */
declare module "*.scss" {
  const styles: string;
  export default styles;
}
