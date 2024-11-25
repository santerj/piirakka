module.exports = {
  purge: ["./piirakka/templates/**/*.{html,js}"],
  darkMode: 'media',
  theme: {
    extend: {
      fontFamily: {
        nunito: ['"Nunito Sans"', 'sans-serif'],
      },
    },
  },
  variants: {
    extend: {},
  },
  plugins: [require('daisyui')],
}
