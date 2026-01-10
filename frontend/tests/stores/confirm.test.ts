import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

describe("useConfirmStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("默认状态正确", async () => {
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const confirm = useConfirmStore();

    expect(confirm.visible).toBe(false);
    expect(confirm.title).toBe("确认");
    expect(confirm.message).toBe("");
    expect(confirm.confirmText).toBe("确认");
    expect(confirm.cancelText).toBe("取消");
    expect(confirm.type).toBe("danger");
    expect(confirm.resolve).toBeUndefined();
  });

  it("show 会填充字段并显示弹窗", async () => {
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const confirm = useConfirmStore();

    const promise = confirm.show({
      message: "确定要删除吗？",
      title: "危险操作",
      confirmText: "删除",
      cancelText: "返回",
      type: "warning",
    });

    expect(confirm.visible).toBe(true);
    expect(confirm.message).toBe("确定要删除吗？");
    expect(confirm.title).toBe("危险操作");
    expect(confirm.confirmText).toBe("删除");
    expect(confirm.cancelText).toBe("返回");
    expect(confirm.type).toBe("warning");
    expect(confirm.resolve).toBeTypeOf("function");

    confirm.cancel();
    await expect(promise).resolves.toBe(false);
  });

  it("show 的缺省参数会使用默认值", async () => {
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const confirm = useConfirmStore();

    const promise = confirm.show({ message: "msg" });

    expect(confirm.visible).toBe(true);
    expect(confirm.message).toBe("msg");
    expect(confirm.title).toBe("确认");
    expect(confirm.confirmText).toBe("确认");
    expect(confirm.cancelText).toBe("取消");
    expect(confirm.type).toBe("danger");

    confirm.confirm();
    await expect(promise).resolves.toBe(true);
  });

  it("confirm 会 resolve true，清理 resolve，并关闭弹窗", async () => {
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const confirm = useConfirmStore();

    const promise = confirm.show({ message: "m" });
    confirm.confirm();

    await expect(promise).resolves.toBe(true);
    expect(confirm.visible).toBe(false);
    expect(confirm.resolve).toBeUndefined();
  });

  it("cancel 会 resolve false，清理 resolve，并关闭弹窗", async () => {
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const confirm = useConfirmStore();

    const promise = confirm.show({ message: "m" });
    confirm.cancel();

    await expect(promise).resolves.toBe(false);
    expect(confirm.visible).toBe(false);
    expect(confirm.resolve).toBeUndefined();
  });

  it("confirm/cancel 在没有 resolve 时也能安全执行", async () => {
    const { useConfirmStore } = await import("../../src/stores/confirm");
    const confirm = useConfirmStore();

    confirm.visible = true;
    confirm.resolve = undefined;

    confirm.confirm();
    expect(confirm.visible).toBe(false);
    expect(confirm.resolve).toBeUndefined();

    confirm.visible = true;
    confirm.cancel();
    expect(confirm.visible).toBe(false);
    expect(confirm.resolve).toBeUndefined();
  });
});

