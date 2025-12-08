/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts}"],
  theme: {
    extend: {
      colors: {
        primary: "#f7f7fb",
        accent: "#6c63ff"
      },
      boxShadow: {
        float: "0 10px 30px rgba(0,0,0,0.08)"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

