/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts}"],
  theme: {
    extend: {
      colors: {
        primary: "#f8f9fb",
        accent: "#1f2937"
      },
      boxShadow: {
        float: "0 10px 30px rgba(0,0,0,0.08)"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

