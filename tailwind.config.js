module.exports = {
  purge: ["./piirakka/templates/**/*.{html,js}"],
  darkMode: "media",
  theme: {
    extend: {
      fontFamily: {
        ebgaramond: ['"EB Garamond"', "serif"],
        hostgrotesk: ['"Host Grotesk"', "sans-serif"],
        chivomono: ['"Chivo Mono"', "monospace"],
      },
    },
  },
  variants: {
    extend: {},
  },
};
