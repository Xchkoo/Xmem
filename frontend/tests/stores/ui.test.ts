import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useUiStore } from "../../src/stores/ui";

/**
 * 初始化 UI store 的测试环境，并启用 fake timers。
 */
const setupUiStore = () => {
  setActivePinia(createPinia());
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-01-10T00:00:00Z"));
  return useUiStore();
};

describe("useUiStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("startRouteTransition 会按时间切换 bar/loading 状态", () => {
    const ui = setupUiStore();

    ui.startRouteTransition();
    expect(ui.routeState).toBe("idle");

    vi.advanceTimersByTime(ui.routeShowBarAfterMs);
    expect(ui.routeState).toBe("bar");

    vi.advanceTimersByTime(ui.routeShowLoadingAfterMs - ui.routeShowBarAfterMs);
    expect(ui.routeState).toBe("loading");
  });

  it("finishRouteTransition 会遵守最短 loading 显示时间", () => {
    const ui = setupUiStore();
    ui.setRouteMinLoadingMs(500);

    ui.startRouteTransition();
    vi.advanceTimersByTime(ui.routeShowLoadingAfterMs);
    expect(ui.routeState).toBe("loading");

    vi.advanceTimersByTime(100);
    ui.finishRouteTransition();
    expect(ui.routeState).toBe("loading");

    vi.advanceTimersByTime(500);
    expect(ui.routeState).toBe("idle");
  });

  it("resetRouteTransition 会清理状态与计时器", () => {
    const ui = setupUiStore();
    ui.startRouteTransition();
    vi.advanceTimersByTime(ui.routeShowBarAfterMs);
    expect(ui.routeState).toBe("bar");

    ui.resetRouteTransition();
    expect(ui.routeState).toBe("idle");
    expect(ui.routeStartedAt).toBeNull();
  });
});

