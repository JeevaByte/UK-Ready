import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // UKReady brand colours — inspired by gov.uk palette
        brand: {
          blue: "#1d70b8",      // gov.uk link blue
          "blue-dark": "#003078", // gov.uk dark blue
          green: "#00703c",     // gov.uk green (success / high confidence)
          amber: "#f47738",     // gov.uk warning amber (medium confidence)
          red: "#d4351c",       // gov.uk red (low confidence / errors)
          "grey-light": "#f3f2f1", // gov.uk light grey (backgrounds)
          "grey-mid": "#b1b4b6",   // gov.uk mid grey
          "grey-dark": "#505a5f",  // gov.uk dark grey (secondary text)
        },
      },
      fontFamily: {
        // GDS Transport font stack (gov.uk official)
        sans: [
          '"GDS Transport"',
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
      },
      animation: {
        "pulse-soft": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
