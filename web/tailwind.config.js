/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        card: "rgb(var(--color-card) / <alpha-value>)",
        fg: "rgb(var(--color-fg) / <alpha-value>)",
        "fg-secondary": "rgb(var(--color-fg-secondary) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
        income: "rgb(var(--color-income) / <alpha-value>)",
        expense: "rgb(var(--color-expense) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
      },
      fontFamily: {
        heading: ["Bricolage Grotesque", "sans-serif"],
        sans: ["Space Grotesk", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      borderRadius: {
        card: "16px",
      },
    },
  },
  plugins: [],
};
