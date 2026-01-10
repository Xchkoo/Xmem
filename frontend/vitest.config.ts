import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.ts"],
    css: false,
    restoreMocks: true,
    mockReset: true,
    clearMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json-summary"],
      include: ["src/{api,components,directives,router,stores,utils}/**/*.{ts,vue}"],
      exclude: ["src/main.ts", "src/env.d.ts", "src/App.vue"],
      thresholds: {
        lines: 23,
        functions: 20,
        branches: 15,
        statements: 23,
      },
    },
  },
});

