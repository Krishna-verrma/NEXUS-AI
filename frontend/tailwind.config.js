/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: '#080B11',
          surface: '#0E131F',
          card: '#131929',
          border: 'rgba(255, 255, 255, 0.08)',
          hover: 'rgba(255, 255, 255, 0.04)',
          cyan: '#00F0FF',
          violet: '#8B5CF6',
          indigo: '#6366F1',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#F43F5E',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'cyan-glow': '0 0 20px -5px rgba(0, 240, 255, 0.3)',
        'violet-glow': '0 0 20px -5px rgba(139, 92, 246, 0.3)',
        'amber-glow': '0 0 20px -5px rgba(245, 158, 11, 0.3)',
      }
    },
  },
  plugins: [],
}
