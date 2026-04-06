import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Open Sans"', "system-ui", "sans-serif"],
      },
      colors: {
        primary: {
          DEFAULT: "#3949a0",
          dark: "#2e3b82",
          light: "#5c6bc0",
          50: "#eef0f9",
          100: "#d4d8f0",
          200: "#a9b1e0",
          300: "#7e8ad1",
          400: "#5c6bc0",
          500: "#3949a0",
          600: "#2e3b82",
          700: "#232d64",
          800: "#181f46",
          900: "#0d1128",
        },
        accent: "#e8a723",
        surface: {
          DEFAULT: "#ffffff",
          secondary: "#f7f8fb",
          border: "#e2e5f1",
        },
        text: {
          DEFAULT: "#333333",
          secondary: "#666666",
          muted: "#999999",
        },
        quartile: {
          q1: "#2e7d32",
          q2: "#1565c0",
          q3: "#e65100",
          q4: "#546e7a",
        },
        type: {
          bg: "#eef0f9",
          text: "#3949a0",
        },
      },
      borderRadius: {
        card: "8px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(57, 73, 160, 0.08)",
        "card-hover": "0 4px 12px rgba(57, 73, 160, 0.15)",
        header: "0 1px 4px rgba(57, 73, 160, 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
