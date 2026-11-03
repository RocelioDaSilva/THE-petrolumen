// @ts-check

const nextEsLintConfigObject = require('eslint-config-next');
const { FlatCompat } = require('@eslint/eslintrc');
const path = require('path');
const typeScriptParser = require('@typescript-eslint/parser');
// const babelParser = require('@babel/eslint-parser'); // May not be needed if next handles JS correctly now

// Determine the directory of the eslint-config-next package
const eslintConfigNextPkgJsonPath = require.resolve('eslint-config-next/package.json');
const eslintConfigNextDir = path.dirname(eslintConfigNextPkgJsonPath);

// console.log(`Directory for eslint-config-next: ${eslintConfigNextDir}`);

// Create a FlatCompat instance specifically for resolving eslint-config-next
const compatForNext = new FlatCompat({
  baseDirectory: eslintConfigNextDir, // Resolve './parser.js' relative to eslint-config-next's directory
  resolvePluginsRelativeTo: eslintConfigNextDir, // Resolve its plugins relative to its own directory
});

// Convert the legacy eslint-config-next object to an array of flat config objects
// This should now correctly resolve './parser.js' to node_modules/eslint-config-next/parser.js
const nextFlatConfigs = compatForNext.config(nextEsLintConfigObject);

/** @type {import('eslint').Linter.FlatConfig[]} */
module.exports = [
  {
    ignores: [
      ".next/",
      "out/",
      "dist/",
      "node_modules/",
      "src-tauri/target/",
    ]
  },

  // Add the configurations derived from eslint-config-next
  ...nextFlatConfigs,

  // Add project-specific TypeScript configuration to ensure correct parsing
  // This might override or supplement parts of nextFlatConfigs for .ts/.tsx files.
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: typeScriptParser, // Explicitly use @typescript-eslint/parser
      parserOptions: {
        project: './tsconfig.json', // Ensure it uses the project's tsconfig
        tsconfigRootDir: __dirname, // Root directory for tsconfig.json
        ecmaFeatures: {
          jsx: true, // Enable JSX parsing for TSX files
        },
      },
    },
    // Add any project-specific rules for TypeScript files here if needed
    // rules: {
    //   "@typescript-eslint/no-explicit-any": "warn",
    // }
  },

  // If you need to further customize JavaScript parsing (e.g., ensure @babel/eslint-parser
  // with specific options), you can add another config block for JS files.
  // However, eslint-config-next (with its internal ./parser.js now correctly resolved)
  // should ideally handle JS files appropriately using @babel/eslint-parser.
  // Example:
  // {
  //   files: ['**/*.js', '**/*.jsx'],
  //   languageOptions: {
  //     parser: babelParser, // require('@babel/eslint-parser')
  //     parserOptions: {
  //       requireConfigFile: false,
  //       babelOptions: {
  //         presets: ["next/babel"],
  //       },
  //     },
  //   },
  // },
];
