/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#0066cc', // Синий цвет Башкирэнерго
        'secondary': '#003366',
        'accent': '#ff6600',
      },
    },
  },
  plugins: [],
}
