import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { nextTick } from "vue";

describe("usePreferencesStore", () => {
  beforeEach(() => {
    vi.resetModules();
    localStorage.clear();
  });

  it("init 会从 localStorage 读取并应用合法值", async () => {
    localStorage.setItem(
      "preferences",
      JSON.stringify({ quickDeleteEnabled: true, noteCopyFormat: "plain" }),
    );

    const { usePreferencesStore } = await import("../../src/stores/preferences");
    setActivePinia(createPinia());
    const prefs = usePreferencesStore();

    prefs.init();
    expect(prefs.quickDeleteEnabled).toBe(true);
    expect(prefs.noteCopyFormat).toBe("plain");
  });

  it("init 会忽略损坏 JSON 与非法字段", async () => {
    localStorage.setItem("preferences", "{not-json");

    const { usePreferencesStore } = await import("../../src/stores/preferences");
    setActivePinia(createPinia());
    const prefs = usePreferencesStore();

    prefs.quickDeleteEnabled = true;
    prefs.noteCopyFormat = "plain";

    prefs.init();
    expect(prefs.quickDeleteEnabled).toBe(true);
    expect(prefs.noteCopyFormat).toBe("plain");
  });

  it("init 会忽略不支持的 noteCopyFormat", async () => {
    localStorage.setItem(
      "preferences",
      JSON.stringify({ quickDeleteEnabled: true, noteCopyFormat: "markdown" }),
    );

    const { usePreferencesStore } = await import("../../src/stores/preferences");
    setActivePinia(createPinia());
    const prefs = usePreferencesStore();

    prefs.init();
    expect(prefs.quickDeleteEnabled).toBe(true);
    expect(prefs.noteCopyFormat).toBe("raw");
  });

  it("变更状态会通过订阅持久化到 localStorage", async () => {
    const { usePreferencesStore } = await import("../../src/stores/preferences");
    setActivePinia(createPinia());
    const prefs = usePreferencesStore();

    prefs.init();
    prefs.setQuickDeleteEnabled(true);
    prefs.setNoteCopyFormat("plain");
    await nextTick();

    expect(localStorage.getItem("preferences")).toBe(
      JSON.stringify({ quickDeleteEnabled: true, noteCopyFormat: "plain" }),
    );
  });

  it("订阅只会被 attach 一次", async () => {
    const { usePreferencesStore } = await import("../../src/stores/preferences");

    setActivePinia(createPinia());
    const prefsA = usePreferencesStore();
    const subSpyA = vi.spyOn(prefsA, "$subscribe");
    prefsA.init();

    setActivePinia(createPinia());
    const prefsB = usePreferencesStore();
    const subSpyB = vi.spyOn(prefsB, "$subscribe");
    prefsB.init();

    expect(subSpyA).toHaveBeenCalledTimes(1);
    expect(subSpyB).toHaveBeenCalledTimes(0);
  });
});
