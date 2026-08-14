/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f5ff',
          100: '#e0ebff',
          200: '#bae0ff',
          300: '#7cc2ff',
          400: '#369eff',
          500: '#0979ff',
          600: '#005be6',
          700: '#0047b3',
          800: '#00378f',
          900: '#002c73',
          950: '#001a47',
        },
        brand: {
          purple: '#6366f1',
          indigo: '#4f46e5',
          cyan: '#06b6d4',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'card-hover': '0 10px 30px -10px rgba(0, 0, 0, 0.1)',
        'dark-card': '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
      }
    },
  },
  plugins: [],
};
