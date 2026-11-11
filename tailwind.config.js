/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./core/**/*.py", "./static/js/main.js"],
  theme: {
    extend: {
      colors: {
        zt: {
          bg: "#050807",
          bg2: "#090F0C",
          card: "#0D1410",
          elevated: "#111A15",
          neon: "#00FF75",
          green: "#00CC66",
          moss: "#123D29",
          text: "#F5F7F5",
          text2: "#A1AAA4",
          muted: "#707A73",
          border: "#1B2921",
          warn: "#FFB547",
          error: "#FF5252",
        },
      },
      fontFamily: {
        sans: ["Inter Variable", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono Variable", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      maxWidth: { site: "80rem" },
      boxShadow: {
        glow: "0 0 0 1px rgba(0,255,117,.25), 0 8px 40px -8px rgba(0,255,117,.35)",
        "glow-sm": "0 0 24px -6px rgba(0,255,117,.45)",
        panel: "0 30px 80px -20px rgba(0,0,0,.8), 0 0 0 1px rgba(27,41,33,1)",
      },
      keyframes: {
        "pulse-dot": { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.35 } },
        blink: { "0%,49%": { opacity: 1 }, "50%,100%": { opacity: 0 } },
        "slide-in": { from: { opacity: 0, transform: "translateY(-6px)" }, to: { opacity: 1, transform: "none" } },
        scan: { "0%": { transform: "translateY(-100%)" }, "100%": { transform: "translateY(100%)" } },
      },
      animation: {
        "pulse-dot": "pulse-dot 2s ease-in-out infinite",
        blink: "blink 1s step-end infinite",
        "slide-in": "slide-in .35s ease-out both",
        scan: "scan 6s linear infinite",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
