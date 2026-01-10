import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { defineComponent, nextTick } from "vue";
import { useConfirmStore } from "../../src/stores/confirm";
import { useDataStore, type LedgerEntry } from "../../src/stores/data";
import { useLedgerEditorStore } from "../../src/stores/ledgerEditor";
import { useToastStore } from "../../src/stores/toast";

/**
 * 刷新微任务与 Vue 渲染队列，便于断言异步逻辑结果。
 */
const flushPromises = async () => {
  await Promise.resolve();
  await nextTick();
};

const LedgerStatsCardStub = defineComponent({
  name: "LedgerStatsCard",
  emits: ["click"],
  template: `<button data-test="stats" @click="$emit('click')">stats</button>`,
});

const CustomSelectStub = defineComponent({
  name: "CustomSelect",
  props: ["modelValue", "options", "placeholder"],
  emits: ["update:modelValue"],
  template: `
    <div>
      <button data-test="set-cat" @click="$emit('update:modelValue', '餐饮美食')">set</button>
    </div>
  `,
});

const LedgerCardContentStub = defineComponent({
  name: "LedgerCardContent",
  props: ["ledger"],
  template: `<div data-test="ledger-content"></div>`,
});

const createLedger = (overrides: Partial<LedgerEntry> = {}): LedgerEntry => {
  return {
    id: 10,
    raw_text: "午餐 23",
    currency: "CNY",
    status: "completed",
    created_at: "2026-01-10T06:30:00Z",
    updated_at: null,
    amount: 23,
    category: "餐饮美食",
    merchant: "便利店",
    event_time: "2026-01-10T05:32:00Z",
    meta: null,
    task_id: null,
    ...overrides,
  };
};

describe("LedgersView", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    vi.spyOn(console, "log").mockImplementation(() => {});
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("挂载会加载第一页，并支持统计卡片跳转", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/ledger/:ledgerId", name: "ledger-view", component: { template: "<div>ledger</div>" } },
        { path: "/statistics", name: "statistics", component: { template: "<div>statistics</div>" } },
      ],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    data.ledgers = [createLedger({ id: 10 })];
    data.ledgerPagination.total = 1;
    data.ledgerPagination.totalPages = 1;
    const fetchSpy = vi.spyOn(data, "fetchLedgers").mockResolvedValue({} as any);

    const LedgersView = (await import("../../src/views/LedgersView.vue")).default;
    const wrapper = mount(LedgersView, {
      global: {
        plugins: [pinia, router],
        stubs: {
          LedgerStatsCard: LedgerStatsCardStub,
          LedgerCardContent: LedgerCardContentStub,
          CustomSelect: CustomSelectStub,
        },
      },
    });

    await flushPromises();
    expect(fetchSpy).toHaveBeenCalled();
    expect(fetchSpy).toHaveBeenCalledWith(undefined, 1, 20);

    const pushSpy = vi.spyOn(router, "push");
    await wrapper.get('[data-test="stats"]').trigger("click");
    expect(pushSpy).toHaveBeenCalledWith({ name: "statistics" });
  }, 10000);

  it("点击卡片会跳转详情，编辑按钮会打开编辑器", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div>home</div>" } },
        { path: "/ledger/:ledgerId", name: "ledger-view", component: { template: "<div>ledger</div>" } },
      ],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    data.ledgers = [createLedger({ id: 11, status: "completed" })];
    data.ledgerPagination.total = 1;
    data.ledgerPagination.totalPages = 1;
    vi.spyOn(data, "fetchLedgers").mockResolvedValue({} as any);

    const editor = useLedgerEditorStore();
    const openSpy = vi.spyOn(editor, "open");

    const LedgersView = (await import("../../src/views/LedgersView.vue")).default;
    const wrapper = mount(LedgersView, {
      global: {
        plugins: [pinia, router],
        stubs: {
          LedgerStatsCard: LedgerStatsCardStub,
          LedgerCardContent: LedgerCardContentStub,
          CustomSelect: CustomSelectStub,
        },
      },
    });
    await flushPromises();

    const pushSpy = vi.spyOn(router, "push");
    await wrapper.get(".card").trigger("click");
    expect(pushSpy).toHaveBeenCalledWith({ name: "ledger-view", params: { ledgerId: 11 } });

    const editBtn = wrapper.find('button[title="编辑"]');
    expect(editBtn.exists()).toBe(true);
    await editBtn.trigger("click");
    expect(openSpy).toHaveBeenCalledWith(expect.objectContaining({ id: 11 }));
  });

  it("删除确认后会调用 removeLedger 并重新加载当前页", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div>home</div>" } }],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    data.ledgers = [createLedger({ id: 12 })];
    data.ledgerPagination.total = 1;
    data.ledgerPagination.totalPages = 1;
    const fetchSpy = vi.spyOn(data, "fetchLedgers").mockResolvedValue({} as any);
    const removeSpy = vi.spyOn(data, "removeLedger").mockResolvedValue(true as any);

    const confirm = useConfirmStore();
    const showSpy = vi.spyOn(confirm, "show").mockResolvedValue(true);

    const toast = useToastStore();
    const toastSuccessSpy = vi.spyOn(toast, "success").mockImplementation(() => "t");

    const LedgersView = (await import("../../src/views/LedgersView.vue")).default;
    const wrapper = mount(LedgersView, {
      global: {
        plugins: [pinia, router],
        stubs: {
          LedgerStatsCard: LedgerStatsCardStub,
          LedgerCardContent: LedgerCardContentStub,
          CustomSelect: CustomSelectStub,
        },
      },
    });
    await flushPromises();

    const deleteBtn = wrapper.find('button[title="删除"]');
    expect(deleteBtn.exists()).toBe(true);
    await deleteBtn.trigger("click");
    await flushPromises();

    expect(showSpy).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalledWith(12);
    expect(toastSuccessSpy).toHaveBeenCalledWith("删除成功");
    expect(fetchSpy.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("分类变化会重新加载，并传递 category 参数", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div>home</div>" } }],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    data.ledgers = [createLedger({ id: 13 })];
    data.ledgerPagination.total = 1;
    data.ledgerPagination.totalPages = 1;
    const fetchSpy = vi.spyOn(data, "fetchLedgers").mockResolvedValue({} as any);

    const LedgersView = (await import("../../src/views/LedgersView.vue")).default;
    const wrapper = mount(LedgersView, {
      global: {
        plugins: [pinia, router],
        stubs: {
          LedgerStatsCard: LedgerStatsCardStub,
          LedgerCardContent: LedgerCardContentStub,
          CustomSelect: CustomSelectStub,
        },
      },
    });
    await flushPromises();
    fetchSpy.mockClear();

    await wrapper.get('[data-test="set-cat"]').trigger("click");
    await flushPromises();

    expect(fetchSpy).toHaveBeenCalledWith("餐饮美食", 1, 20);
  });
});
