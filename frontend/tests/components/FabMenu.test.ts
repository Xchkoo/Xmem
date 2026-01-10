import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import FabMenu from "../../src/components/FabMenu.vue";

let reloadSpy: ReturnType<typeof vi.fn>;

describe("FabMenu", () => {
  beforeEach(() => {
    reloadSpy = vi.fn();
    vi.stubGlobal("location", { reload: reloadSpy } as any);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("默认不展开子菜单", () => {
    const wrapper = mount(FabMenu, {
      global: {
        stubs: { Teleport: true, "transition-group": false },
      },
    });

    expect(wrapper.text()).not.toContain("主界面");
    expect(wrapper.text()).not.toContain("笔记库");
    expect(wrapper.text()).not.toContain("记账库");
    expect(wrapper.text()).not.toContain("待办事项");
    expect(wrapper.text()).not.toContain("统计");
    expect(wrapper.text()).not.toContain("设置");
  });

  it("点击主菜单按钮会展开与收起子菜单", async () => {
    const wrapper = mount(FabMenu, {
      global: {
        stubs: { Teleport: true, "transition-group": false },
      },
    });

    const [refreshButton, toggleButton] = wrapper.findAll("button.fab-main");
    expect(refreshButton.exists()).toBe(true);
    expect(toggleButton.exists()).toBe(true);

    await toggleButton.trigger("click");
    expect(wrapper.text()).toContain("主界面");
    expect(wrapper.text()).toContain("设置");

    await toggleButton.trigger("click");
    expect(wrapper.text()).not.toContain("主界面");
  });

  it("点击菜单项会触发对应的 emits", async () => {
    const wrapper = mount(FabMenu, {
      global: {
        stubs: { Teleport: true, "transition-group": false },
      },
    });

    const [, toggleButton] = wrapper.findAll("button.fab-main");
    await toggleButton.trigger("click");

    await wrapper.findAll("button.fab-sub").find((b) => b.text().includes("笔记库"))!.trigger("click");
    await wrapper.findAll("button.fab-sub").find((b) => b.text().includes("设置"))!.trigger("click");

    expect(wrapper.emitted("notes")).toBeTruthy();
    expect(wrapper.emitted("settings")).toBeTruthy();
  });

  it("点击刷新按钮会调用 location.reload", async () => {
    const wrapper = mount(FabMenu, {
      global: {
        stubs: { Teleport: true, "transition-group": false },
      },
    });

    const [refreshButton] = wrapper.findAll("button.fab-main");
    await refreshButton.trigger("click");
    expect(reloadSpy).toHaveBeenCalledTimes(1);
  });
});
