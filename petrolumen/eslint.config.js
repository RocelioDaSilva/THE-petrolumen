// @ts-check

const nextEsLintConfig = require('eslint-config-next');
// const { FlatCompat } = require('@eslint/eslintrc'); // Only if needed for legacy configs

// const compat = new FlatCompat({
//   baseDirectory: __dirname,
// });

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
  // Spread the Next.js default configurations
  // eslint-config-next should export an array for flat config
  ...nextEsLintConfig,

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
