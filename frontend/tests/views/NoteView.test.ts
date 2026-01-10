import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("md-editor-v3", () => ({
  MdPreview: { name: "MdPreview", template: `<div data-test="md-preview"></div>`, props: ["modelValue"] },
}));
vi.mock("md-editor-v3/lib/style.css", () => ({}));

describe("NoteView", () => {
  beforeEach(() => {
    vi.resetModules();
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("在 note 存在时支持返回、编辑与复制", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/editor/:noteId?", name: "editor", component: { template: "<div>editor</div>" } },
      ],
    });
    await router.push("/");
    await router.isReady();

    const { useDataStore } = await import("../../src/stores/data");
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const { useToastStore } = await import("../../src/stores/toast");
    const { usePreferencesStore } = await import("../../src/stores/preferences");
    const data = useDataStore();
    const confirm = useConfirmStore();
    const toast = useToastStore();
    const prefs = usePreferencesStore();

    data.notes = [{ id: 1, body_md: "**hi**", created_at: "2026-01-10T00:00:00Z" }];
    prefs.noteCopyFormat = "plain";
    confirm.visible = false;

    const writeSpy = vi.fn(async () => {});
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeSpy },
      configurable: true,
    });
    const toastSpy = vi.spyOn(toast, "success").mockImplementation(() => "t");

    const backSpy = vi.spyOn(router, "back");
    const pushSpy = vi.spyOn(router, "push");

    const NoteView = (await import("../../src/views/NoteView.vue")).default;
    const wrapper = mount(NoteView, {
      props: { noteId: 1 },
      global: {
        plugins: [router],
        directives: { "secure-display": {} as any },
        stubs: { ConfirmDialog: { template: "<div />" } },
      },
    });

    expect(wrapper.text()).toContain("查看笔记");
    expect(wrapper.findAll('[data-test="md-preview"]').length).toBe(1);

    const headerButtons = wrapper.findAll("header button");
    const backBtn = headerButtons.find((b) => b.text().includes("返回"));
    const editBtn = headerButtons.find((b) => b.text().includes("编辑"));
    expect(backBtn).toBeTruthy();
    expect(editBtn).toBeTruthy();

    await backBtn!.trigger("click");
    expect(backSpy).toHaveBeenCalledTimes(1);

    await editBtn!.trigger("click");
    expect(pushSpy).toHaveBeenCalledWith({ name: "editor", params: { noteId: 1 } });

    const copyBtn = wrapper.findAll("button").find((b) => b.text().includes("复制"));
    expect(copyBtn).toBeTruthy();
    await copyBtn!.trigger("click");

    expect(writeSpy).toHaveBeenCalled();
    expect(toastSpy).toHaveBeenCalled();
  });

  it("删除确认后会调用 removeNote、emit deleted 并返回上一页", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div>home</div>" } }],
    });
    await router.push("/");
    await router.isReady();

    const { useDataStore } = await import("../../src/stores/data");
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const { useToastStore } = await import("../../src/stores/toast");
    const data = useDataStore();
    const confirm = useConfirmStore();
    const toast = useToastStore();

    data.notes = [{ id: 2, body_md: "x", created_at: "2026-01-10T00:00:00Z" }];
    const removeSpy = vi.spyOn(data, "removeNote").mockResolvedValue(undefined as any);
    const showSpy = vi.spyOn(confirm, "show").mockResolvedValue(true);
    const toastSpy = vi.spyOn(toast, "success").mockImplementation(() => "t");
    const backSpy = vi.spyOn(router, "back");

    const NoteView = (await import("../../src/views/NoteView.vue")).default;
    const wrapper = mount(NoteView, {
      props: { noteId: 2 },
      global: {
        plugins: [router],
        directives: { "secure-display": {} as any },
        stubs: { ConfirmDialog: { template: "<div />" } },
      },
    });

    const deleteBtn = wrapper.findAll("button").find((b) => b.text().includes("删除"));
    expect(deleteBtn).toBeTruthy();
    await deleteBtn!.trigger("click");
    await new Promise((r) => setTimeout(r, 0));

    expect(showSpy).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalledWith(2);
    expect(toastSpy).toHaveBeenCalled();
    expect(wrapper.emitted("deleted")?.length).toBe(1);
    expect(backSpy).toHaveBeenCalled();
  });
});
