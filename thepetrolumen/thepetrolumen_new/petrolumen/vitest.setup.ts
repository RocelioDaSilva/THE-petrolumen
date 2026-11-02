import '@testing-library/jest-dom';
// You can add other global setup here if needed, for example:
// - Mocking global objects (fetch, localStorage, etc.)
// - Setting up a global store for tests that need it (though often done per-test or per-suite)

// Example: Mocking localStorage if used by Zustand persist middleware
// const localStorageMock = (() => {
//   let store: { [key: string]: string } = {};
//   return {
//     getItem: (key: string) => store[key] || null,
//     setItem: (key: string, value: string) => {
//       store[key] = value.toString();
//     },
//     removeItem: (key: string) => {
//       delete store[key];
//     },
//     clear: () => {
//       store = {};
//     },
//   };
// })();
// Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// If you use matchers from jest-dom in TypeScript, you might need to extend Vitest's `Expect` interface.
// This is often handled by including "vitest/globals" or specific matcher types in tsconfig.json's "types" array,
// or by ensuring your test files (or this setup file) correctly import what's needed for type inference.
// For `@testing-library/jest-dom`, simply importing it usually suffices for Vitest to pick up the matchers.
// If type errors occur for matchers like .toBeInTheDocument(), you might need to add:
// import type { TestingLibraryMatchers } from "@testing-library/jest-dom/matchers";
// import type { ExpectStatic } from 'vitest';
// declare module 'vitest' {
//   interface Assertion<T = any> extends TestingLibraryMatchers<typeof expect.stringContaining, T> {}
//   interface AsymmetricMatchersContaining extends Testing-libraryMatchers<typeof expect.stringContaining, T> {}
// }
// However, with modern Vitest and @testing-library/jest-dom, this manual type extension is often not necessary.
// Let's start without it and add if type errors arise.
