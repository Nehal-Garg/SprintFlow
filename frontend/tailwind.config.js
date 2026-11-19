/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          black: '#101010',
          charcoal: '#171717',
          green: '#75C900',
          greenHover: '#66B000',
          white: '#FFFFFF',
          surface: '#F5F5F5',
          border: '#E5E5E5',
          muted: '#737373',
          success: '#16A34A',
          warning: '#F59E0B',
          error: '#DC2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(16, 16, 16, 0.05), 0 1px 2px rgba(16, 16, 16, 0.03)',
        elevated: '0 10px 25px -5px rgba(16, 16, 16, 0.12), 0 4px 10px -4px rgba(16, 16, 16, 0.06)',
      },
    },
  },
  plugins: [],
};
