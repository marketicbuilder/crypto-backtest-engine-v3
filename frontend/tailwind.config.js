/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'rgb(2 6 23)',
        foreground: 'rgb(241 245 249)',
        border: 'rgb(30 41 59)',
        card: 'rgb(15 23 42 / 0.6)',
        primary: { DEFAULT: 'rgb(56 189 248)', foreground: 'rgb(2 6 23)' },
        success: 'rgb(52 211 153)',
        danger: 'rgb(244 63 94)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
