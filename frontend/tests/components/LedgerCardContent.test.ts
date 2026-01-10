import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import LedgerCardContent from "../../src/components/LedgerCardContent.vue";
import type { LedgerEntry } from "../../src/stores/data";

const createLedger = (overrides: Partial<LedgerEntry> = {}): LedgerEntry => {
  return {
    id: 1,
    raw_text: "午餐花费 23 元",
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

describe("LedgerCardContent", () => {
  it("在 pending 状态显示待识别文案", () => {
    vi.spyOn(Date.prototype, "toLocaleString").mockReturnValue("1月10日 14:30");

    const wrapper = mount(LedgerCardContent, {
      props: { ledger: createLedger({ status: "pending", amount: undefined }) },
    });

    expect(wrapper.text()).toContain("待识别");
  });

  it("优先展示 event_time 并生成快照", () => {
    const toLocaleSpy = vi.spyOn(Date.prototype, "toLocaleString").mockReturnValue("1月10日 13:32");

    const wrapper = mount(LedgerCardContent, {
      props: { ledger: createLedger({ event_time: "2026-01-10T05:32:00Z", created_at: "2026-01-10T06:30:00Z" }) },
    });

    expect(toLocaleSpy).toHaveBeenCalled();
    expect(wrapper.html()).toMatchSnapshot();
  });

  it("raw_text 超长时会截断并追加省略号", () => {
    vi.spyOn(Date.prototype, "toLocaleString").mockReturnValue("1月10日 13:32");

    const longText = "a".repeat(150);
    const wrapper = mount(LedgerCardContent, {
      props: { ledger: createLedger({ raw_text: longText }) },
    });

    expect(wrapper.text()).toContain("……");
  });
});

