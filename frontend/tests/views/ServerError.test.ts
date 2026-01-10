import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import ServerError from "../../src/views/ServerError.vue";

describe("ServerError", () => {
  it("回到首页按钮会 router.replace 到 home", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/500", name: "server-error", component: ServerError },
      ],
    });

    await router.push({ name: "server-error" });
    await router.isReady();

    const replaceSpy = vi.spyOn(router, "replace");
    const wrapper = mount(ServerError, { global: { plugins: [router] } });

    const homeBtn = wrapper.findAll("button").find((b) => b.text().includes("回到首页"));
    expect(homeBtn).toBeTruthy();
    await homeBtn!.trigger("click");

    expect(replaceSpy).toHaveBeenCalledWith({ name: "home" });
  });

  it("刷新页面按钮会调用 window.location.reload", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/500", name: "server-error", component: ServerError },
      ],
    });

    await router.push({ name: "server-error" });
    await router.isReady();

    const wrapper = mount(ServerError, { global: { plugins: [router] } });
    const reloadBtn = wrapper.findAll("button").find((b) => b.text().includes("刷新页面"));
    expect(reloadBtn).toBeTruthy();

    const originalLocation = window.location;
    const reload = vi.fn();
    Object.defineProperty(window, "location", {
      value: { reload },
      configurable: true,
    });

    await reloadBtn!.trigger("click");

    expect(reload).toHaveBeenCalledTimes(1);
    Object.defineProperty(window, "location", { value: originalLocation });
  });
});
