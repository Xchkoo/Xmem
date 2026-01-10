import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

describe("TabSwitcher", () => {
  it("会渲染 tabs，并在点击时发出 update:modelValue", async () => {
    const TabSwitcher = (await import("../../src/components/TabSwitcher.vue")).default;

    const wrapper = mount(TabSwitcher, {
      props: {
        tabs: [
          { label: "A", value: "a" },
          { label: "B", value: "b" },
        ],
        modelValue: "a",
      },
      slots: { default: "<div data-test='slot'>slot</div>" },
    });

    expect(wrapper.text()).toContain("A");
    expect(wrapper.text()).toContain("B");
    expect(wrapper.find('[data-test="slot"]').exists()).toBe(true);

    const buttons = wrapper.findAll("button");
    expect(buttons).toHaveLength(2);

    await buttons[1].trigger("click");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["b"]);
  });

  it("高亮当前 modelValue 对应的 tab", async () => {
    const TabSwitcher = (await import("../../src/components/TabSwitcher.vue")).default;

    const wrapper = mount(TabSwitcher, {
      props: {
        tabs: [
          { label: "笔记", value: "note" },
          { label: "记账", value: "ledger" },
        ],
        modelValue: "ledger",
      },
    });

    const buttons = wrapper.findAll("button");
    expect(buttons[0].classes().join(" ")).not.toContain("bg-gray-900");
    expect(buttons[1].classes().join(" ")).toContain("bg-gray-900");
  });
});

