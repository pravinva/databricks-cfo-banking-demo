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
          bg: 'hsl(220 20% 97%)',
          surface: '#ffffff',
          border: '#e3e8eb',
          orange: 'hsl(152 55% 41%)',
          amber: 'hsl(38 95% 52%)',
          text: '#111827',
          'text-dim': '#6b7280',
          green: 'hsl(152 55% 41%)',
          red: 'hsl(0 72% 52%)',
          blue: 'hsl(217 91% 60%)',
        },
        primary: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          500: 'hsl(152 55% 41%)',
          600: '#208c57',
          700: '#1f724b',
          900: '#0f3c29',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        mono: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
      borderRadius: {
        md: '0.75rem',
        lg: '0.75rem',
        xl: '0.75rem',
      },
    },
  },
  plugins: [],
}

export default config
