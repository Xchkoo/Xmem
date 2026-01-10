import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import LedgerEditor from "../../src/components/LedgerEditor.vue";
import { useDataStore } from "../../src/stores/data";
import { useToastStore } from "../../src/stores/toast";
import type { LedgerEntry } from "../../src/stores/data";

const createLedger = (overrides: Partial<LedgerEntry> = {}): LedgerEntry => {
  return {
    id: 7,
    raw_text: "午餐 23 元",
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

describe("LedgerEditor integration", () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
  });

  it("点击保存会调用 store.updateLedger，并处理 event_time", async () => {
    const data = useDataStore();
    const toast = useToastStore();
    const updateSpy = vi.spyOn(data, "updateLedger").mockResolvedValue(createLedger());
    const toastSpy = vi.spyOn(toast, "success").mockImplementation(() => "toast-id");

    const wrapper = mount(LedgerEditor, {
      props: {
        visible: true,
        ledger: createLedger(),
      },
      global: {
        plugins: [pinia],
        stubs: {
          CustomSelect: {
            template: `<select />`,
            props: ["modelValue", "options"],
            emits: ["update:modelValue"],
          },
          transition: false,
        },
      },
    });

    const eventTimeInput = wrapper.get('input[type="datetime-local"]');
    const localValue = "2026-01-10T15:32";
    await eventTimeInput.setValue(localValue);

    const buttons = wrapper.findAll("button");
    const saveButton = buttons.find((b) => b.text().includes("保存"));
    expect(saveButton).toBeTruthy();
    await saveButton!.trigger("click");

    await new Promise((r) => setTimeout(r, 0));

    expect(updateSpy).toHaveBeenCalledTimes(1);
    expect(updateSpy.mock.calls[0]?.[0]).toBe(7);
    expect(updateSpy.mock.calls[0]?.[1]).toMatchObject({
      event_time: new Date(localValue).toISOString(),
    });
    expect(toastSpy).toHaveBeenCalledWith("保存成功");
  });

  it("API 报错时会 toast.error 并保持健壮", async () => {
    const data = useDataStore();
    const toast = useToastStore();
    vi.spyOn(data, "updateLedger").mockRejectedValue({ response: { data: { detail: "bad request" } } });
    const errorSpy = vi.spyOn(toast, "error").mockImplementation(() => "toast-id");

    const wrapper = mount(LedgerEditor, {
      props: {
        visible: true,
        ledger: createLedger(),
      },
      global: {
        plugins: [pinia],
        stubs: {
          CustomSelect: {
            template: `<select />`,
            props: ["modelValue", "options"],
            emits: ["update:modelValue"],
          },
          transition: false,
        },
      },
    });

    const buttons = wrapper.findAll("button");
    const saveButton = buttons.find((b) => b.text().includes("保存"));
    expect(saveButton).toBeTruthy();
    await saveButton!.trigger("click");
    await new Promise((r) => setTimeout(r, 0));

    expect(errorSpy).toHaveBeenCalledWith("bad request");
  });
});
