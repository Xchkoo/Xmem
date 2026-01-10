import { afterEach, vi } from "vitest";

if (!("matchMedia" in window)) {
  Object.defineProperty(window, "matchMedia", {
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
    writable: true,
  });
}

if (!("ResizeObserver" in window)) {
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // @ts-expect-error - polyfill for tests
  window.ResizeObserver = ResizeObserver;
}

afterEach(() => {
  vi.useRealTimers();
});

