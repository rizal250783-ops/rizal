module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        emerald: {
          50: "#ECFDF5", 500: "#10B981", 600: "#059669",
          700: "#047857", 800: "#065F46", 900: "#064E3B",
        },
        gold: {
          100: "#FEF3C7", 500: "#F59E0B", 600: "#D97706", 700: "#B45309", 800: "#92400E",
        },
      },
      fontFamily: {
        heading: ["'Plus Jakarta Sans'", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
