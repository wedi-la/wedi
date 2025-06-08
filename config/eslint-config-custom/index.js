module.exports = {
  extends: ["eslint:recommended", "prettier", "turbo"],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
  },
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  rules: {
    "no-console": ["warn", { allow: ["warn", "error"] }],
    "no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
  },
  ignorePatterns: [
    "node_modules/",
    "dist/",
    ".next/",
    "coverage/",
    ".turbo/",
  ],
}; 