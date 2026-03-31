import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0f3460",
        accent: "#e94560",
        "header-start": "#1a1a2e",
        "header-mid": "#16213e",
        "header-end": "#0f3460",
        surface: "#f0f2f5",
        "q1-green": "#27ae60",
        "q2-blue": "#2980b9",
        "q3-orange": "#f39c12",
        "q4-gray": "#95a5a6",
        "type-bg": "#e8eaf6",
        "type-text": "#3f51b5",
      },
    },
  },
  plugins: [],
};

export default config;
