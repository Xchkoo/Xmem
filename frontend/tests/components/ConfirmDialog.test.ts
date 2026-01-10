import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ConfirmDialog from "../../src/components/ConfirmDialog.vue";

describe("ConfirmDialog", () => {
  it("visible=false 时不渲染内容", () => {
    const wrapper = mount(ConfirmDialog, {
      props: { visible: false, message: "m" },
      global: { stubs: { Teleport: true, Transition: false } },
    });

    expect(wrapper.find(".confirm-overlay").exists()).toBe(false);
  });

  it("点击确认/取消会发出事件", async () => {
    const wrapper = mount(ConfirmDialog, {
      props: { visible: true, message: "m", title: "t", confirmText: "ok", cancelText: "no" },
      global: { stubs: { Teleport: true, Transition: false } },
    });

    const buttons = wrapper.findAll("button");
    const cancelBtn = buttons.find((b) => b.text() === "no");
    const confirmBtn = buttons.find((b) => b.text() === "ok");
    expect(cancelBtn).toBeTruthy();
    expect(confirmBtn).toBeTruthy();

    await cancelBtn!.trigger("click");
    expect(wrapper.emitted("cancel")?.length).toBe(1);

    await confirmBtn!.trigger("click");
    expect(wrapper.emitted("confirm")?.length).toBe(1);
  });

  it("点击遮罩层本身会触发 cancel", async () => {
    const wrapper = mount(ConfirmDialog, {
      props: { visible: true, message: "m" },
      global: { stubs: { Teleport: true, Transition: false } },
    });

    await wrapper.get(".confirm-overlay").trigger("click");
    expect(wrapper.emitted("cancel")?.length).toBe(1);
  });

  it("type=warning 会应用对应按钮样式", () => {
    const wrapper = mount(ConfirmDialog, {
      props: { visible: true, message: "m", type: "warning" },
      global: { stubs: { Teleport: true, Transition: false } },
    });

    const confirmBtn = wrapper.findAll("button").at(1);
    expect(confirmBtn).toBeTruthy();
    expect(confirmBtn!.classes().join(" ")).toContain("bg-yellow-500");
  });
});

