import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#4cd7f6",
        secondary: "#4edea3",
        surface: "#0b1326",
        "surface-dim": "#0b1326",
        "surface-container": "#171f33",
        "surface-container-low": "#131b2e",
        "surface-container-lowest": "#060e20",
        "surface-container-high": "#222a3d",
        "surface-container-highest": "#2d3449",
        "on-surface": "#dae2fd",
        "on-surface-variant": "#bcc9cd",
        "outline-variant": "#3d494c",
        error: "#ffb4ab",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "sans-serif"],
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "monospace"],
      },
      spacing: {
        gutter: "16px",
        "container-padding": "12px",
        margin: "24px",
      },
    },
  },
  plugins: [],
};

export default config;
