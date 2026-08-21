/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        tradly: {
          bg: "#06080D",
          canvas: "#040609",
          card: "#0C101A",
          "card-raised": "#121826",
          border: "#182238",
          "border-bright": "#253454",
          hover: "#141D2E",
          accent: "#00F0FF",
          "accent-glow": "rgba(0, 240, 255, 0.15)",
          bullish: "#00E676",
          "bullish-glow": "rgba(0, 230, 118, 0.15)",
          bearish: "#FF1744",
          "bearish-glow": "rgba(255, 23, 68, 0.15)",
          warning: "#FFB300",
          text: "#E6EDF8",
          secondary: "#8B9BB4",
          muted: "#5A6B85",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "JetBrains Mono", "monospace"],
      },
      boxShadow: {
        "neon-cyan": "0 0 25px -5px rgba(0, 240, 255, 0.35)",
        "neon-emerald": "0 0 25px -5px rgba(0, 230, 118, 0.35)",
        "neon-red": "0 0 25px -5px rgba(255, 23, 68, 0.35)",
        "glass-inset": "inset 0 1px 1px 0 rgba(255, 255, 255, 0.08)",
        "card-depth": "0 10px 30px -10px rgba(0, 0, 0, 0.7), 0 0 1px 1px rgba(255, 255, 255, 0.05)",
      },
      animation: {
        "radar-sweep": "radar 4s linear infinite",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "scanline": "scanline 8s linear infinite",
        "shimmer": "shimmer 2.5s ease-in-out infinite",
      },
      keyframes: {
        radar: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.4", transform: "scale(1)" },
          "50%": { opacity: "0.8", transform: "scale(1.05)" },
        },
        scanline: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(1000%)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
