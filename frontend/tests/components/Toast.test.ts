import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import Toast from "../../src/components/Toast.vue";
import { useToastStore } from "../../src/stores/toast";

describe("Toast", () => {
  it("会渲染 store 中的 toast，并支持手动关闭", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const toastStore = useToastStore();

    toastStore.toasts = [
      { id: "t1", message: "hello", type: "success" },
      { id: "t2", message: "oops", type: "error" },
    ];

    const removeSpy = vi.spyOn(toastStore, "remove");

    const wrapper = mount(Toast, {
      global: { plugins: [pinia], stubs: { Teleport: true, TransitionGroup: false } },
    });

    expect(wrapper.text()).toContain("hello");
    expect(wrapper.text()).toContain("oops");

    const items = wrapper.findAll(".toast-item");
    expect(items.length).toBe(2);
    expect(items[0]!.classes().join(" ")).toContain("bg-green-500");
    expect(items[1]!.classes().join(" ")).toContain("bg-red-500");

    const firstCloseBtn = items[0]!.find("button");
    await firstCloseBtn.trigger("click");
    expect(removeSpy).toHaveBeenCalledWith("t1");
  });
});

