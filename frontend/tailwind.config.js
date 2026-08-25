/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#0A192F",
          light: "#132a4d",
          soft: "#1e3a63",
        },
        gold: {
          DEFAULT: "#D4AF37",
          light: "#E5C158",
          dark: "#B8942B",
        },
      },
      fontFamily: {
        heading: ["Outfit", "sans-serif"],
        body: ["'Plus Jakarta Sans'", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(10,25,47,0.08), 0 1px 2px rgba(10,25,47,0.04)",
      },
    },
  },
  plugins: [],
};
