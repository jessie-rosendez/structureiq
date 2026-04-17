import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        brand: {
          blue: "#0066CC",
          "blue-dark": "#004F9F",
          "blue-light": "#EBF4FF",
          "blue-mid": "#CCE3F5",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          secondary: "#F5F7FA",
          tertiary: "#EEF1F5",
        },
        border: {
          DEFAULT: "#DDE2E8",
          strong: "#B0BAC4",
        },
        ink: {
          DEFAULT: "#111827",
          secondary: "#374151",
          muted: "#6B7280",
          subtle: "#9CA3AF",
        },
        status: {
          "pass-bg": "#ECFDF5",
          "pass-text": "#047857",
          "pass-border": "#6EE7B7",
          "warn-bg": "#FFFBEB",
          "warn-text": "#92400E",
          "warn-border": "#FCD34D",
          "fail-bg": "#FEF2F2",
          "fail-text": "#991B1B",
          "fail-border": "#FCA5A5",
          "neutral-bg": "#F9FAFB",
          "neutral-text": "#374151",
          "neutral-border": "#D1D5DB",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px -1px rgba(0,0,0,0.06)",
        "card-md": "0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.06)",
        "card-lg": "0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.05)",
      },
    },
  },
  plugins: [],
};
export default config;
