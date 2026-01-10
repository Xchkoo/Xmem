import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter, type RouteRecordRaw } from "vue-router";
import { defineComponent, nextTick } from "vue";

describe("Vue Router", () => {
  it("支持路由跳转与参数传递", async () => {
    const Target = defineComponent({
      template: `<div data-test="target">ledger: {{ $route.params.ledgerId }}</div>`,
    });

    const routes: RouteRecordRaw[] = [
      { path: "/ledger/:ledgerId", name: "ledger-view", component: Target },
    ];

    const router = createRouter({
      history: createMemoryHistory(),
      routes,
    });

    const App = defineComponent({ template: `<router-view />` });
    const wrapper = mount(App, { global: { plugins: [router] } });

    await router.push({ name: "ledger-view", params: { ledgerId: "42" } });
    await router.isReady();
    await nextTick();

    expect(wrapper.get('[data-test="target"]').text()).toContain("42");
  });

  it("支持导航守卫重定向", async () => {
    const Login = defineComponent({ template: `<div data-test="login">login</div>` });
    const Protected = defineComponent({ template: `<div data-test="protected">protected</div>` });

    const routes: RouteRecordRaw[] = [
      { path: "/login", name: "login", component: Login },
      { path: "/protected", name: "protected", component: Protected, meta: { requiresAuth: true } },
    ];

    const router = createRouter({
      history: createMemoryHistory(),
      routes,
    });

    router.beforeEach((to) => {
      if (to.meta.requiresAuth) return { name: "login" };
      return true;
    });

    const App = defineComponent({ template: `<router-view />` });
    const wrapper = mount(App, { global: { plugins: [router] } });

    await router.push({ name: "protected" });
    await router.isReady();

    expect(wrapper.get('[data-test="login"]').text()).toBe("login");
  });
});
