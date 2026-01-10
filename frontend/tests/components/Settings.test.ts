import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { defineComponent, nextTick } from "vue";
import { useUserStore } from "../../src/stores/user";
import { usePreferencesStore } from "../../src/stores/preferences";
import { useLedgerEditorStore } from "../../src/stores/ledgerEditor";

/**
 * 根据按钮文本查找并返回对应按钮包装器。
 */
const getButtonByText = (wrapper: any, text: string) => {
  const btn = wrapper.findAll("button").find((b: any) => b.text().trim() === text);
  if (!btn) {
    throw new Error(`未找到按钮: ${text}`);
  }
  return btn;
};

/**
 * 等待一轮异步更新，配合 router.replace 等异步流程断言。
 */
const flushPromises = () => new Promise((r) => setTimeout(r, 0));

describe("Settings", () => {
  beforeEach(() => {
    vi.resetModules();
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it("点击遮罩或关闭按钮会触发 close", async () => {
    const Settings = (await import("../../src/components/Settings.vue")).default;
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/login", name: "login", component: { template: "<div />" } }],
    });
    await router.push("/login");
    await router.isReady();

    const wrapper = mount(Settings, {
      props: { visible: true },
      global: {
        plugins: [router],
        stubs: {
          ChangePasswordDialog: defineComponent({
            name: "ChangePasswordDialog",
            props: ["visible"],
            emits: ["close", "saved"],
            template: `<div v-if="visible" data-test="cpd" />`,
          }),
        },
      },
    });

    await wrapper.get(".fixed.inset-0").trigger("click");
    expect(wrapper.emitted("close")).toBeTruthy();

    await getButtonByText(wrapper, "×").trigger("click");
    expect(wrapper.emitted("close")!.length).toBeGreaterThanOrEqual(2);
  });

  it("修改密码按钮会切换 ChangePasswordDialog 显示并可关闭", async () => {
    const Settings = (await import("../../src/components/Settings.vue")).default;
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/login", name: "login", component: { template: "<div />" } }],
    });
    await router.push("/login");
    await router.isReady();

    const wrapper = mount(Settings, {
      props: { visible: true },
      global: {
        plugins: [router],
        stubs: {
          ChangePasswordDialog: defineComponent({
            name: "ChangePasswordDialog",
            props: ["visible"],
            emits: ["close", "saved"],
            template: `<div v-if="visible" data-test="cpd" @click="$emit('close')" />`,
          }),
        },
      },
    });

    await wrapper.findAll("button").find((b) => b.text().includes("修改密码"))!.trigger("click");
    expect(wrapper.find('[data-test="cpd"]').exists()).toBe(true);

    await wrapper.get('[data-test="cpd"]').trigger("click");
    await nextTick();
    expect(wrapper.find('[data-test="cpd"]').exists()).toBe(false);
  });

  it("切换偏好设置会更新 preferences store", async () => {
    const Settings = (await import("../../src/components/Settings.vue")).default;
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/login", name: "login", component: { template: "<div />" } }],
    });
    await router.push("/login");
    await router.isReady();

    const preferences = usePreferencesStore();
    const quickDeleteSpy = vi.spyOn(preferences, "setQuickDeleteEnabled");
    const copyFormatSpy = vi.spyOn(preferences, "setNoteCopyFormat");

    const wrapper = mount(Settings, {
      props: { visible: true },
      global: {
        plugins: [router],
        stubs: {
          ChangePasswordDialog: defineComponent({
            name: "ChangePasswordDialog",
            props: ["visible"],
            emits: ["close", "saved"],
            template: `<div />`,
          }),
        },
      },
    });

    const checkboxes = wrapper.findAll('input[type="checkbox"]');
    expect(checkboxes.length).toBeGreaterThanOrEqual(2);

    await checkboxes[0].setValue(true);
    expect(quickDeleteSpy).toHaveBeenCalledWith(true);
    expect(preferences.quickDeleteEnabled).toBe(true);

    await checkboxes[1].setValue(true);
    expect(copyFormatSpy).toHaveBeenCalledWith("plain");
    expect(preferences.noteCopyFormat).toBe("plain");

    await checkboxes[1].setValue(false);
    expect(copyFormatSpy).toHaveBeenCalledWith("raw");
    expect(preferences.noteCopyFormat).toBe("raw");
  });

  it("退出登录会关闭编辑器、调用 logout 并跳转 login 携带 redirect", async () => {
    const Settings = (await import("../../src/components/Settings.vue")).default;
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/home", name: "home", component: { template: "<div />" } },
        { path: "/login", name: "login", component: { template: "<div />" } },
      ],
    });
    await router.push("/home?tab=note");
    await router.isReady();

    const user = useUserStore();
    user.profile = { id: 1, email: "a@b.com", user_name: "u" };
    const logoutSpy = vi.spyOn(user, "logout").mockImplementation(() => {});

    const ledgerEditor = useLedgerEditorStore();
    const closeSpy = vi.spyOn(ledgerEditor, "close");

    const replaceSpy = vi.spyOn(router, "replace");

    const wrapper = mount(Settings, {
      props: { visible: true },
      global: {
        plugins: [router],
        stubs: {
          ChangePasswordDialog: defineComponent({
            name: "ChangePasswordDialog",
            props: ["visible"],
            emits: ["close", "saved"],
            template: `<div />`,
          }),
        },
      },
    });

    await wrapper.findAll("button").find((b) => b.text().includes("退出登录"))!.trigger("click");
    await flushPromises();
    await nextTick();

    expect(closeSpy).toHaveBeenCalledTimes(1);
    expect(logoutSpy).toHaveBeenCalledTimes(1);
    expect(replaceSpy).toHaveBeenCalled();
    expect(router.currentRoute.value.name).toBe("login");
    expect(router.currentRoute.value.query.redirect).toBe("/home?tab=note");
    expect(wrapper.emitted("close")).toBeTruthy();
  });
});

