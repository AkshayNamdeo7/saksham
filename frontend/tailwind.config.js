/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        navy: {
          DEFAULT: '#0b2545',
          50: '#f0f4fa',
          100: '#dce7f3',
          200: '#bdd2e8',
          300: '#92b3d6',
          400: '#628cc0',
          500: '#416eaa',
          600: '#31578e',
          700: '#2a4771',
          800: '#1b2f5c',
          900: '#12233f',
        },
        ink: {
          900: '#0f172a',
          700: '#1e293b',
          500: '#475569',
          400: '#64748b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Inter', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(15,23,42,0.06), 0 1px 3px rgba(15,23,42,0.10)',
        elevated: '0 4px 6px -1px rgba(15,23,42,0.07), 0 2px 4px -2px rgba(15,23,42,0.05)',
      },
      borderRadius: {
        xl: '0.9rem',
        '2xl': '1.15rem',
      },
    },
  },
  plugins: [],
}