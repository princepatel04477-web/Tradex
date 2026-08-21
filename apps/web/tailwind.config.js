/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        tradly: {
          bg: "#0B0E14",
          card: "#121722",
          border: "#1E2638",
          hover: "#1A2234",
          accent: "#00F0FF",
          bullish: "#00E676",
          bearish: "#FF1744",
          warning: "#FF9100",
          text: "#E2E8F0",
          muted: "#94A3B8"
        }
      }
    },
  },
  plugins: [],
}
