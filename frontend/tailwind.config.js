/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Warm charcoal surfaces
        ink: {
          950: '#0a0a0b',
          900: '#111113',
          850: '#161619',
          800: '#1c1c20',
          700: '#27272d',
          600: '#3a3a42',
          500: '#55555f',
        },
        // Text
        fg: {
          DEFAULT: '#ecebe7',
          muted: '#a3a19b',
          subtle: '#6f6e69',
        },
        // Single accent: champagne gold
        gold: {
          100: '#f8eedb',
          200: '#f2dfb8',
          300: '#eacb8d',
          400: '#ddb36a',
          500: '#c79a4a',
          600: '#a47c36',
        },
        ok: '#93c29f',
        bad: '#e38c84',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['"Instrument Serif"', 'ui-serif', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-up': 'fadeUp 0.45s cubic-bezier(0.2, 0.7, 0.2, 1) both',
      },
    },
  },
  plugins: [],
}
