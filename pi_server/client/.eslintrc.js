module.exports = {
  root: true,

  env: {
    node: true,
  },

  extends: ["plugin:vue/essential", "@vue/airbnb"],

  parserOptions: {
    parser: "babel-eslint",
  },

  rules: {
    "no-console": "off",
    "no-debugger": "off",
    quotes: [2, "double"],
    "vue/singleline-html-element-content-newline": ["ignore"],
    "vue/multiline-html-element-content-newline": ["ignore"],
    "vue/html-self-closing": [
      "error",
      {
        html: {
          void: "any",
          normal: "always",
          component: "always",
        },
      },
    ],
  },

  extends: ["plugin:vue/strongly-recommended", "@vue/airbnb"],
};
