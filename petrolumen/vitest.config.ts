/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path'; // To resolve aliases like @/

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true, // Enables global APIs like describe, it, expect
    environment: 'jsdom', // Use JSDOM for DOM-related tests
    setupFiles: './vitest.setup.ts', // Path to setup file for extending expect, etc.
    css: true, // If your components import CSS files
    alias: {
      '@': path.resolve(__dirname, './'), // To match Next.js path alias for @/*
    },
  },
});
