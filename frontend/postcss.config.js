/**
 * PostCSS configuration.
 *
 * Tailwind generates the utility classes, autoprefixer adds vendor prefixes
 * according to the browserslist defaults.
 */
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
