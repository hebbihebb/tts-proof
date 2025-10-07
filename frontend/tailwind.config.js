/** @type {import('tailwindcss').Config} */
export default {
  content: [
  './index.html',
  './src/**/*.{js,ts,jsx,tsx}'
],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Catppuccin Macchiato Color Palette
        catppuccin: {
          // Base colors
          base: "#24273a",
          mantle: "#1e2030", 
          crust: "#181926",
          
          // Surface colors
          surface0: "#363a4f",
          surface1: "#494d64",
          surface2: "#5b6078",
          
          // Overlay colors
          overlay0: "#6e738d",
          overlay1: "#8087a2",
          overlay2: "#939ab7",
          
          // Text colors
          subtext0: "#a5adcb",
          subtext1: "#b8c0e0",
          text: "#cad3f5",
          
          // Accent colors
          rosewater: "#f4dbd6",
          flamingo: "#f0c6c6", 
          pink: "#f5bde6",
          mauve: "#c6a0f6",
          red: "#ed8796",
          maroon: "#ee99a0",
          peach: "#f5a97f",
          yellow: "#eed49f",
          green: "#a6da95",
          teal: "#8bd5ca",
          sky: "#91d7e3",
          sapphire: "#7dc4e4",
          blue: "#8aadf4",
          lavender: "#b7bdf8",
        },
        
        // Light theme colors (Catppuccin Latte-inspired)
        light: {
          base: "#eff1f5",
          mantle: "#e6e9ef",
          crust: "#dce0e8",
          surface0: "#ccd0da",
          surface1: "#bcc0cc",
          surface2: "#acb0be",
          text: "#4c4f69",
          subtext1: "#5c5f77",
          subtext0: "#6c6f85",
        },
        
        // Legacy primary colors (keep for compatibility)
        primary: {
          50: "#f0f9ff",
          100: "#e0f2fe", 
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
        },
      },
      boxShadow: {
        'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        'soft-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03)',
      },
    },
  },
  plugins: [],
}