/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease-out',
        'slide-in-left': 'slideInLeft 0.6s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'shimmer': 'shimmer 2s infinite',
      },
      keyframes: {
        fadeInUp: {
          'from': {
            opacity: '0',
            transform: 'translateY(30px)',
          },
          'to': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        slideInLeft: {
          'from': {
            opacity: '0',
            transform: 'translateX(-30px)',
          },
          'to': {
            opacity: '1',
            transform: 'translateX(0)',
          },
        },
        float: {
          '0%, 100%': {
            transform: 'translateY(0px)',
          },
          '50%': {
            transform: 'translateY(-10px)',
          },
        },
        shimmer: {
          '0%': {
            'background-position': '-200px 0',
          },
          '100%': {
            'background-position': 'calc(200px + 100%) 0',
          },
        },
      },
    },
  },
  plugins: [],
}