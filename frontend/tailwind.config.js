/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        'slide-in': {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'slide-in': 'slide-in 0.2s ease-out',
      },
      colors: {
        // Stitch Design System
        primary: "#4b7c60",        // Forest green
        "primary-dark": "#3d6b50",  // Primary dark
        "primary-deep": "#2f5a40",  // Primary deep
        terracotta: "#c06c52",      // Terracotta accent
        sage: "#8da399",            // Sage gray-green
        "bg-light": "#F7F5F2",      // Beige background
        "bg-dark": "#161c19",       // Dark background
        border: "#E5EAE7",          // Subtle borders
        "text-muted": "#6b7280",    // Muted text
        "nav-text": "#d1fae5",      // Light nav text
      }
    },
  },
  plugins: [],
}
