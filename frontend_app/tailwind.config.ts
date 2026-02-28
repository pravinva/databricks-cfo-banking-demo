import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bloomberg: {
          bg: '#f4f7f8',
          surface: '#ffffff',
          border: '#e3e8eb',
          orange: '#d97706',
          amber: '#f59e0b',
          text: '#111827',
          'text-dim': '#6b7280',
          green: '#0f9d78',
          red: '#c24141',
          blue: '#2563eb',
        },
        primary: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          500: '#ff8c00',
          600: '#ea580c',
          700: '#c2410c',
          900: '#7c2d12',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        mono: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
