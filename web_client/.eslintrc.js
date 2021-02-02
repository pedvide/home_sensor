module.exports = {
  root: true,

  env: {
    node: true,
  },

  extends: ["plugin:vue/essential", "plugin:vue/strongly-recommended", "@vue/airbnb"],

  parserOptions: {
    parser: "babel-eslint",
  },

  rules: {
    "no-console": "off",
    "no-debugger": "off",
    "comma-dangle": "off",
    quotes: [2, "double"],
    "vue/singleline-html-element-content-newline": [0],
    "vue/multiline-html-element-content-newline": [0],
    "vue/max-attributes-per-line": [0],
    "vue/html-self-closing": [
      2,
      {
        html: {
          void: "any",
          normal: "always",
          component: "always",
        },
      },
    ],
  },
};
