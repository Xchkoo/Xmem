import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { nextTick } from "vue";

const flushPromises = () => new Promise((r) => setTimeout(r, 0));

let loginSpy: ReturnType<typeof vi.fn>;
let registerSpy: ReturnType<typeof vi.fn>;

vi.mock("../../src/stores/user", () => ({
  useUserStore: () => ({
    login: (...args: any[]) => loginSpy(...args),
    register: (...args: any[]) => registerSpy(...args),
  }),
}));

describe("Auth", () => {
  beforeEach(() => {
    vi.resetModules();
    loginSpy = vi.fn(async () => {});
    registerSpy = vi.fn(async () => {});
  });

  it("login 模式默认不显示昵称与确认密码输入", async () => {
    const Auth = (await import("../../src/components/Auth.vue")).default;

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/login", name: "login", component: Auth },
        { path: "/register", name: "register", component: Auth },
        { path: "/todos", name: "todos", component: { template: "<div>todos</div>" } },
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
      ],
    });

    await router.push({ name: "login" });
    await router.isReady();

    const wrapper = mount(Auth, {
      global: { plugins: [router], stubs: { AppFooter: { template: "<div />" } } },
    });

    expect(wrapper.text()).toContain("登录");
    expect(wrapper.find('input[placeholder="请输入昵称（可选）"]').exists()).toBe(false);
    expect(wrapper.find('input[placeholder="请再次输入密码"]').exists()).toBe(false);
  });

  it("切换模式会更新路由并清理注册相关字段", async () => {
    const Auth = (await import("../../src/components/Auth.vue")).default;

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/login", name: "login", component: Auth },
        { path: "/register", name: "register", component: Auth },
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
      ],
    });

    await router.push({ name: "login", query: { redirect: "/todos" } });
    await router.isReady();

    const wrapper = mount(Auth, {
      global: { plugins: [router], stubs: { AppFooter: { template: "<div />" } } },
    });

    await wrapper.get('button[type="button"]').trigger("click");
    await flushPromises();
    await nextTick();

    expect(router.currentRoute.value.name).toBe("register");
    expect(router.currentRoute.value.query.redirect).toBe("/todos");
    expect(wrapper.find('input[placeholder="请输入昵称（可选）"]').exists()).toBe(true);
    expect(wrapper.find('input[placeholder="请再次输入密码"]').exists()).toBe(true);
  });

  it("注册时密码不一致会提示错误且不调用 register", async () => {
    const Auth = (await import("../../src/components/Auth.vue")).default;

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/register", name: "register", component: Auth },
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
      ],
    });

    await router.push({ name: "register" });
    await router.isReady();

    const wrapper = mount(Auth, {
      global: { plugins: [router], stubs: { AppFooter: { template: "<div />" } } },
    });

    await wrapper.get('input[placeholder="请输入邮箱"]').setValue("a@b.com");
    await wrapper.get('input[placeholder="请输入密码"]').setValue("p1");
    await wrapper.get('input[placeholder="请再次输入密码"]').setValue("p2");
    await wrapper.get("form").trigger("submit");

    expect(wrapper.text()).toContain("两次输入的密码不一致");
    expect(registerSpy).not.toHaveBeenCalled();
  });

  it("登录成功会调用 login 并按 redirect 跳转", async () => {
    const Auth = (await import("../../src/components/Auth.vue")).default;

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/login", name: "login", component: Auth },
        { path: "/todos", name: "todos", component: { template: "<div>todos</div>" } },
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
      ],
    });

    await router.push({ name: "login", query: { redirect: "/todos" } });
    await router.isReady();

    const wrapper = mount(Auth, {
      global: { plugins: [router], stubs: { AppFooter: { template: "<div />" } } },
    });

    await wrapper.get('input[placeholder="请输入邮箱"]').setValue("a@b.com");
    await wrapper.get('input[placeholder="请输入密码"]').setValue("pw");
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    await nextTick();

    expect(loginSpy).toHaveBeenCalledWith("a@b.com", "pw");
    expect(router.currentRoute.value.name).toBe("todos");
  });
});
