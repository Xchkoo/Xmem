import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import NotFound from "../../src/views/NotFound.vue";

describe("NotFound", () => {
  it("历史栈不足时，返回上一页会回到首页", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/404", name: "not-found", component: NotFound },
      ],
    });

    await router.push({ name: "not-found" });
    await router.isReady();

    const replaceSpy = vi.spyOn(router, "replace");
    const backSpy = vi.spyOn(router, "back");

    const historyLengthDesc = Object.getOwnPropertyDescriptor(window.history, "length");
    try {
      Object.defineProperty(window.history, "length", { value: 1, configurable: true });

      const wrapper = mount(NotFound, { global: { plugins: [router] } });
      const backBtn = wrapper.findAll("button").find((b) => b.text().includes("返回上一页"));
      expect(backBtn).toBeTruthy();
      await backBtn!.trigger("click");

      expect(backSpy).not.toHaveBeenCalled();
      expect(replaceSpy).toHaveBeenCalledWith({ name: "home" });
    } finally {
      if (historyLengthDesc) {
        Object.defineProperty(window.history, "length", historyLengthDesc);
      }
    }
  });

  it("历史栈充足时，返回上一页会调用 router.back", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/404", name: "not-found", component: NotFound },
      ],
    });

    await router.push({ name: "not-found" });
    await router.isReady();

    const replaceSpy = vi.spyOn(router, "replace");
    const backSpy = vi.spyOn(router, "back");

    const historyLengthDesc = Object.getOwnPropertyDescriptor(window.history, "length");
    try {
      Object.defineProperty(window.history, "length", { value: 2, configurable: true });

      const wrapper = mount(NotFound, { global: { plugins: [router] } });
      const backBtn = wrapper.findAll("button").find((b) => b.text().includes("返回上一页"));
      expect(backBtn).toBeTruthy();
      await backBtn!.trigger("click");

      expect(backSpy).toHaveBeenCalledTimes(1);
      expect(replaceSpy).not.toHaveBeenCalled();
    } finally {
      if (historyLengthDesc) {
        Object.defineProperty(window.history, "length", historyLengthDesc);
      }
    }
  });

  it("回到首页按钮会 router.replace 到 home", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/404", name: "not-found", component: NotFound },
      ],
    });

    await router.push({ name: "not-found" });
    await router.isReady();

    const replaceSpy = vi.spyOn(router, "replace");
    const wrapper = mount(NotFound, { global: { plugins: [router] } });

    const homeBtn = wrapper.findAll("button").find((b) => b.text().includes("回到首页"));
    expect(homeBtn).toBeTruthy();
    await homeBtn!.trigger("click");

    expect(replaceSpy).toHaveBeenCalledWith({ name: "home" });
  });
});

