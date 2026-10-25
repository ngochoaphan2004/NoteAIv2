/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"SF Pro Text"',
          '"SF Pro Display"',
          '"SF Pro"',
          "system-ui",
          '"Helvetica Neue"',
          '"Segoe UI"',
          "Roboto",
          "sans-serif",
        ],
        mono: [
          '"SF Mono"',
          "Monaco",
          "Menlo",
          "Consolas",
          '"JetBrains Mono"',
          "monospace",
        ],
      },
      colors: {
        apple: {
          lightBg: "#f5f5f7",
          darkBg: "#1c1c1e",
          cardLight: "#ffffff",
          cardDark: "#2c2c2e",
          textLight: "#1d1d1f",
          textDark: "#f5f5f7",
          subtextLight: "#86868b",
          subtextDark: "#a1a1a6",
          blue: "#0071e3",
          blueHover: "#0077ed",
          blueDark: "#2997ff",
          green: "#34c759",
          orange: "#ff9500",
          red: "#ff3b30",
        },
      },
    },
  },
  plugins: [],
};
