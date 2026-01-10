import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { defineComponent, nextTick } from "vue";
import { useDataStore } from "../../src/stores/data";
import { useToastStore } from "../../src/stores/toast";
import { usePreferencesStore } from "../../src/stores/preferences";

/**
 * 刷新微任务与 Vue 渲染队列，便于断言异步逻辑结果。
 */
const flushPromises = async () => {
  await Promise.resolve();
  await nextTick();
};

const NoteCardContentStub = defineComponent({
  name: "NoteCardContent",
  props: ["note", "searchQuery"],
  emits: ["copy", "delete", "pin", "edit"],
  template: `
    <div>
      <button data-test="copy" @click="$emit('copy')">copy</button>
      <button data-test="delete" @click="$emit('delete')">delete</button>
      <button data-test="pin" @click="$emit('pin')">pin</button>
      <button data-test="edit" @click="$emit('edit')">edit</button>
    </div>
  `,
});

describe("NotesView", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("挂载会拉取笔记，并支持返回与新增按钮导航", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/editor", name: "editor", component: { template: "<div>editor</div>" } },
        { path: "/note/:noteId", name: "note-view", component: { template: "<div>note</div>" } },
      ],
    });

    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    const fetchSpy = vi.spyOn(data, "fetchNotes").mockResolvedValue(undefined as any);

    const NotesView = (await import("../../src/views/NotesView.vue")).default;
    const wrapper = mount(NotesView, {
      global: {
        plugins: [pinia, router],
        stubs: { NoteCardContent: NoteCardContentStub },
      },
    });

    await flushPromises();
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(fetchSpy).toHaveBeenCalledWith();

    const pushSpy = vi.spyOn(router, "push");
    const headerButtons = wrapper.findAll("header button");
    const backBtn = headerButtons.find((b) => b.text().includes("返回"));
    const addBtn = headerButtons.find((b) => b.text().includes("添加新笔记"));
    expect(backBtn).toBeTruthy();
    expect(addBtn).toBeTruthy();

    await backBtn!.trigger("click");
    expect(pushSpy).toHaveBeenCalledWith("/");

    await addBtn!.trigger("click");
    expect(pushSpy).toHaveBeenCalledWith("/editor");
  });

  it("搜索防抖会按 query 调用 fetchNotes，清空时加载全部", async () => {
    vi.useFakeTimers();
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div>home</div>" } }],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    data.notes = [{ id: 1, body_md: "x", created_at: "2026-01-10T00:00:00Z" }];
    const fetchSpy = vi.spyOn(data, "fetchNotes").mockResolvedValue(undefined as any);

    const NotesView = (await import("../../src/views/NotesView.vue")).default;
    const wrapper = mount(NotesView, {
      global: { plugins: [pinia, router], stubs: { NoteCardContent: NoteCardContentStub } },
    });

    const input = wrapper.get('input[placeholder="搜索笔记..."]');
    await input.setValue("  abc  ");
    vi.advanceTimersByTime(300);
    await flushPromises();
    expect(fetchSpy).toHaveBeenCalledWith("abc");

    await input.setValue("");
    vi.advanceTimersByTime(300);
    await flushPromises();
    expect(fetchSpy).toHaveBeenCalledWith();
  });

  it("点击卡片会跳转详情，并能处理 copy/delete/pin 交互", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/note/:noteId", name: "note-view", component: { template: "<div>note</div>" } },
      ],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    const toast = useToastStore();
    const prefs = usePreferencesStore();
    prefs.noteCopyFormat = "plain";
    data.notes = [{ id: 1, body_md: "**hi**", created_at: "2026-01-10T00:00:00Z" }];

    vi.spyOn(data, "fetchNotes").mockResolvedValue(undefined as any);
    const removeSpy = vi.spyOn(data, "removeNote").mockResolvedValue(true as any);
    const pinSpy = vi.spyOn(data, "togglePinNote").mockResolvedValue({} as any);
    const toastSuccessSpy = vi.spyOn(toast, "success").mockImplementation(() => "t");

    const writeSpy = vi.fn(async () => {});
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeSpy },
      configurable: true,
    });

    const NotesView = (await import("../../src/views/NotesView.vue")).default;
    const wrapper = mount(NotesView, {
      global: { plugins: [pinia, router], stubs: { NoteCardContent: NoteCardContentStub } },
    });
    await flushPromises();

    const pushSpy = vi.spyOn(router, "push");
    await wrapper.get(".card").trigger("click");
    expect(pushSpy).toHaveBeenCalledWith({ name: "note-view", params: { noteId: 1 } });

    await wrapper.get('[data-test="copy"]').trigger("click");
    await flushPromises();
    expect(writeSpy).toHaveBeenCalled();
    expect(toastSuccessSpy).toHaveBeenCalled();

    await wrapper.get('[data-test="delete"]').trigger("click");
    await flushPromises();
    expect(removeSpy).toHaveBeenCalledWith(1);
    expect(toastSuccessSpy).toHaveBeenCalled();

    await wrapper.get('[data-test="pin"]').trigger("click");
    await flushPromises();
    expect(pinSpy).toHaveBeenCalledWith(1);
    expect(toastSuccessSpy).toHaveBeenCalled();
  });
});
