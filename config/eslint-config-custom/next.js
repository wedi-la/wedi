module.exports = {
  extends: [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "./index.js",
  ],
  rules: {
    "@next/next/no-html-link-for-pages": "off",
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-var-requires": "off",
  },
}; 