/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        surface: {
          50: 'hsl(220, 30%, 98%)',
          100: 'hsl(220, 25%, 95%)',
          200: 'hsl(220, 20%, 88%)',
          700: 'hsl(220, 20%, 20%)',
          800: 'hsl(220, 25%, 14%)',
          900: 'hsl(220, 28%, 9%)',
          950: 'hsl(220, 30%, 6%)',
        },
        accent: {
          DEFAULT: 'hsl(262, 83%, 58%)',
          foreground: '#ffffff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
      },
      boxShadow: {
        glow: '0 0 20px rgba(59, 130, 246, 0.15)',
        'glow-lg': '0 0 40px rgba(59, 130, 246, 0.2)',
        card: '0 1px 3px rgba(0,0,0,0.15), 0 4px 16px rgba(0,0,0,0.1)',
      },
    },
  },
  plugins: [],
}
