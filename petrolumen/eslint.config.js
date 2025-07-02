// @ts-check

const nextEsLintConfig = require('eslint-config-next');
const { FlatCompat } = require('@eslint/eslintrc');
const path = require('path'); // Needed for FlatCompat

// nextEsLintConfig is already defined at the top of the file.

const baseDirectory = __dirname; // path.resolve(__dirname) might be more robust depending on execution context
const compat = new FlatCompat({
  baseDirectory: baseDirectory,
  resolvePluginsRelativeTo: baseDirectory, // Important for plugin resolution from the old config
});

/** @type {import('eslint').Linter.FlatConfig[]} */
module.exports = [
  {
    ignores: [
      ".next/",
      "out/",
      "dist/",
      "node_modules/",
      // Add other specific files or directories to ignore if needed
      // e.g., "src-tauri/target/" (though ESLint might not look there anyway)
    ]
  },
  // Convert and spread the Next.js eslintrc-style configurations
  // nextEsLintConfig might be the config object itself, or inside .default
  ...compat.config(nextEsLintConfig.default || nextEsLintConfig),

  // Custom project-specific configurations can be added below
  // For example, to ensure TypeScript project reference is correctly set up
  // (though eslint-config-next should handle this for files it targets)
  {
    files: ['**/*.ts', '**/*.tsx'], // Glob pattern for your TypeScript files
    languageOptions: {
      parserOptions: {
        project: true, // Automatically finds tsconfig.json relative to eslint.config.js
        tsconfigRootDir: __dirname,
      },
    },
    // You can add or override rules specifically for your TS/TSX files here
    // rules: {
    //   "@typescript-eslint/no-unused-vars": "warn",
    // },
  },

  // Example: Add global rules or settings if necessary
  // {
  //   rules: {
  //     "no-console": "warn", // Example: warn about console.log
  //   }
  // }
];
