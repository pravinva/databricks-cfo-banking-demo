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
          bg: '#000000',
          surface: '#1a1a1a',
          border: '#333333',
          orange: '#ff8c00',
          amber: '#ffb347',
          text: '#ffffff',
          'text-dim': '#999999',
          green: '#00ff00',
          red: '#ff0000',
          blue: '#00a0ff',
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
        sans: ['"Courier New"', 'Monaco', 'Menlo', 'monospace'],
        mono: ['"Courier New"', 'Monaco', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}

export default config
