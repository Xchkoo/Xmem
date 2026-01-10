import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { defineComponent, nextTick } from "vue";
import type { LedgerStatistics } from "../../src/stores/data";
import { useDataStore } from "../../src/stores/data";

vi.mock("echarts/core", () => ({ use: vi.fn() }));
vi.mock("echarts/renderers", () => ({ CanvasRenderer: {} }));
vi.mock("echarts/charts", () => ({ BarChart: {} }));
vi.mock("echarts/components", () => ({
  TitleComponent: {},
  TooltipComponent: {},
  GridComponent: {},
}));
vi.mock("vue-echarts", () => {
  return {
    default: defineComponent({
      name: "VChart",
      props: ["option", "autoresize"],
      template: `<div class="v-chart-stub">{{ JSON.stringify(option) }}</div>`,
    }),
  };
});

/**
 * 构造一份最小的 LedgerStatistics 测试数据。
 */
const createStatistics = (overrides: Partial<LedgerStatistics> = {}): LedgerStatistics => {
  return {
    monthly_data: [],
    yearly_data: [],
    category_stats: [],
    current_month_total: 0,
    last_month_total: 0,
    month_diff: 0,
    month_diff_percent: 0,
    ...overrides,
  };
};

/**
 * 等待一轮异步更新，用于 onMounted 异步逻辑。
 */
const flushPromises = () => new Promise((r) => setTimeout(r, 0));

describe("LedgerStatsCard", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("没有 monthly_data 时显示暂无数据", async () => {
    const data = useDataStore();
    vi.spyOn(data, "fetchLedgerStatistics").mockResolvedValue(createStatistics());

    const LedgerStatsCard = (await import("../../src/components/LedgerStatsCard.vue")).default;

    const wrapper = mount(LedgerStatsCard);

    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain("暂无数据");
  });

  it("有数据时会渲染图表并计算总支出", async () => {
    const data = useDataStore();
    vi.spyOn(data, "fetchLedgerStatistics").mockResolvedValue(
      createStatistics({
        monthly_data: [
          { month: "2025-01", amount: 1200, count: 3 },
          { month: "2025-02", amount: 3400, count: 4 },
        ],
      }),
    );

    const LedgerStatsCard = (await import("../../src/components/LedgerStatsCard.vue")).default;

    const wrapper = mount(LedgerStatsCard);

    await flushPromises();
    await nextTick();

    const expectedTotal = (1200 + 3400).toLocaleString();
    expect(wrapper.text()).toContain(`¥${expectedTotal}`);
    expect(wrapper.find(".v-chart-stub").exists()).toBe(true);
    expect(wrapper.find(".v-chart-stub").text()).toContain("1月");
    expect(wrapper.find(".v-chart-stub").text()).toContain("2月");
  });

  it("点击卡片会触发 click 事件", async () => {
    const data = useDataStore();
    vi.spyOn(data, "fetchLedgerStatistics").mockResolvedValue(createStatistics());

    const LedgerStatsCard = (await import("../../src/components/LedgerStatsCard.vue")).default;
    const wrapper = mount(LedgerStatsCard);

    await wrapper.trigger("click");
    expect(wrapper.emitted("click")).toBeTruthy();
  });
});
