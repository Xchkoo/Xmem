import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import LoadingOverlay from "../../src/components/LoadingOverlay.vue";

describe("LoadingOverlay", () => {
  it("visible=false 时不显示遮罩", () => {
    const wrapper = mount(LoadingOverlay, {
      props: { visible: false },
    });

    expect(wrapper.find('[role="status"]').exists()).toBe(false);
  });

  it("visible=true 时会在 delayMs 后显示遮罩", async () => {
    vi.useFakeTimers();

    const wrapper = mount(LoadingOverlay, {
      props: { visible: true, delayMs: 200 },
    });

    expect(wrapper.find('[role="status"]').exists()).toBe(false);
    vi.advanceTimersByTime(199);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[role="status"]').exists()).toBe(false);

    vi.advanceTimersByTime(1);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[role="status"]').exists()).toBe(true);
  });

  it("切回 visible=false 会清理计时器并隐藏遮罩", async () => {
    vi.useFakeTimers();

    const wrapper = mount(LoadingOverlay, {
      props: { visible: true, delayMs: 300 },
    });

    vi.advanceTimersByTime(150);
    await wrapper.setProps({ visible: false });
    vi.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[role="status"]').exists()).toBe(false);
  });
});

