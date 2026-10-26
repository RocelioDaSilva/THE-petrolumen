import '@testing-library/jest-dom';

// Global ResizeObserver mock for Radix UI and slider components in jsdom environment
if (typeof window !== 'undefined' && !window.ResizeObserver) {
  class ResizeObserverMock {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.ResizeObserver = ResizeObserverMock as any;
  global.ResizeObserver = ResizeObserverMock as any;
}
