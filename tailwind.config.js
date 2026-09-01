module.exports = {
  purge: ["./piirakka/templates/**/*.{html,js}"],
  darkMode: "media",
  theme: {
    extend: {
      fontFamily: {
        nunito: ['"Nunito Sans"', "sans-serif"],
        ebgaramond: ['"EB Garamond"', "serif"],
        hostgrotesk: ['"Host Grotesk"', "sans-serif"],
      },
    },
  },
  variants: {
    extend: {},
  },
};
