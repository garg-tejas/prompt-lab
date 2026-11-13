// TypeScript checks types and symbols; ESLint checks React hook correctness.
module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  plugins: ["react-hooks"],
  extends: ["plugin:react-hooks/recommended"],
  ignorePatterns: ["dist/", "node_modules/", ".deps-before-ui-20261025/"],
}
