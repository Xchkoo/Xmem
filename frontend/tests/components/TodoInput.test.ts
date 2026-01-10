import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { nextTick } from "vue";
import { useDataStore } from "../../src/stores/data";
import { useToastStore } from "../../src/stores/toast";

/**
 * 刷新微任务与 Vue 渲染队列，便于断言异步逻辑结果。
 */
const flushPromises = async () => {
  await Promise.resolve();
  await nextTick();
};

describe("TodoInput", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("点击添加：空文本会提示 warning；合法文本会调用 addTodo 并清空输入", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const data = useDataStore();
    const toast = useToastStore();
    const addSpy = vi.spyOn(data, "addTodo").mockResolvedValue({ id: 1 } as any);
    const warningSpy = vi.spyOn(toast, "warning").mockImplementation(() => "t");

    const TodoInput = (await import("../../src/components/TodoInput.vue")).default;
    const wrapper = mount(TodoInput, { global: { plugins: [pinia] } });

    const addBtn = wrapper.get("button");
    await addBtn.trigger("click");
    expect(warningSpy).toHaveBeenCalledWith("待办内容不能为空");

    const input = wrapper.get("input");
    await input.setValue("hello");
    await addBtn.trigger("click");
    await flushPromises();

    expect(addSpy).toHaveBeenCalledWith("hello");
    expect((input.element as HTMLInputElement).value).toBe("");
  });

  it("点击添加：超过 50 字会提示 warning 且不调用 addTodo", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const data = useDataStore();
    const toast = useToastStore();
    const addSpy = vi.spyOn(data, "addTodo").mockResolvedValue({ id: 1 } as any);
    const warningSpy = vi.spyOn(toast, "warning").mockImplementation(() => "t");

    const TodoInput = (await import("../../src/components/TodoInput.vue")).default;
    const wrapper = mount(TodoInput, { global: { plugins: [pinia] } });

    const input = wrapper.get("input");
    await input.setValue("a".repeat(51));

    const addBtn = wrapper.get("button");
    await addBtn.trigger("click");
    expect(addBtn.attributes("disabled")).toBeDefined();
    expect(warningSpy).not.toHaveBeenCalled();
    expect(addSpy).not.toHaveBeenCalled();
  });

  it("按回车会创建组与首个子待办，并派发 focus-first-item 事件", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const data = useDataStore();
    const toast = useToastStore();
    vi.spyOn(toast, "error").mockImplementation(() => "t");

    const addSpy = vi
      .spyOn(data, "addTodo")
      .mockImplementationOnce(async (title: string) => ({ id: 10, title } as any))
      .mockImplementationOnce(async (title: string, groupId?: number) => ({ id: 11, title, group_id: groupId } as any));

    const dispatchSpy = vi.spyOn(window, "dispatchEvent");

    const TodoInput = (await import("../../src/components/TodoInput.vue")).default;
    const wrapper = mount(TodoInput, { global: { plugins: [pinia] } });

    const input = wrapper.get("input");
    await input.setValue("Group");
    await input.trigger("keydown.enter");
    await flushPromises();

    expect(addSpy).toHaveBeenCalledWith("Group");
    expect(addSpy).toHaveBeenCalledWith("新建待办", 10);
    expect(dispatchSpy).toHaveBeenCalled();
    const eventArg = dispatchSpy.mock.calls[0]?.[0] as CustomEvent;
    expect(eventArg.type).toBe("focus-first-item");
    expect((eventArg as any).detail.groupId).toBe(10);
  });
});
