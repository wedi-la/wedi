module.exports = {
  extends: [
    "plugin:@typescript-eslint/recommended",
    "./index.js",
  ],
  rules: {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-non-null-assertion": "warn",
  },
}; 