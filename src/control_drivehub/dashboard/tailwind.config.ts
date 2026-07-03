import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0f1419",
        panel: "#1a2332",
        accent: "#3b82f6",
        danger: "#ef4444",
        ok: "#22c55e",
        warn: "#f59e0b",
      },
    },
  },
  plugins: [],
};

export default config;
