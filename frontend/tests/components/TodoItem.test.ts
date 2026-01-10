import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { Todo } from "../../src/stores/data";

/**
 * 构造待办数据，便于覆盖不同状态下的 UI/事件分支。
 */
const createTodo = (overrides: Partial<Todo> = {}): Todo => {
  return {
    id: 1,
    title: "t",
    completed: false,
    is_pinned: false,
    group_id: null,
    group_items: undefined,
    created_at: "2026-01-10T00:00:00Z",
    ...overrides,
  };
};

/**
 * 获取 TodoItem 内用于编辑标题的输入框（排除复选框）。
 */
const getTitleInput = (wrapper: any) => {
  const inputs = wrapper.findAll("input");
  const titleInput = inputs.find((i: any) => (i.element as HTMLInputElement).type !== "checkbox");
  if (!titleInput) {
    throw new Error(`未找到标题输入框，当前 inputs 数量: ${inputs.length}`);
  }
  return titleInput;
};

describe("TodoItem", () => {
  it("勾选、置顶、删除会发出对应事件", async () => {
    const TodoItem = (await import("../../src/components/TodoItem.vue")).default;
    const wrapper = mount(TodoItem, {
      props: { todo: createTodo({ id: 7, title: "hello" }) },
    });

    await wrapper.get('input[type="checkbox"]').trigger("change");
    expect(wrapper.emitted("toggle")?.[0]).toEqual([7]);

    const pinBtn = wrapper.find('button[title="置顶"]');
    expect(pinBtn.exists()).toBe(true);
    await pinBtn.trigger("click");
    expect(wrapper.emitted("pin")?.[0]).toEqual([7]);

    const deleteBtn = wrapper.find('button[title="删除待办"]');
    expect(deleteBtn.exists()).toBe(true);
    await deleteBtn.trigger("click");
    expect(wrapper.emitted("delete")?.[0]).toEqual([7]);
  });

  it("编辑标题：blur/enter 会在内容变化时发出 update-title，esc 会回滚", async () => {
    const TodoItem = (await import("../../src/components/TodoItem.vue")).default;
    const wrapper = mount(TodoItem, {
      props: { todo: createTodo({ id: 2, title: "old" }) },
    });

    const input = getTitleInput(wrapper);
    await input.setValue("  new  ");
    await input.trigger("blur");
    expect(wrapper.emitted("update-title")?.[0]).toEqual([2, "new"]);

    await input.setValue("something");
    await input.trigger("keydown.esc");
    expect((input.element as HTMLInputElement).value).toBe("old");

    await input.setValue("x");
    await input.trigger("keydown.enter");
    expect(wrapper.emitted("update-title")?.[1]).toEqual([2, "x"]);
  });

  it("已完成待办不允许置顶与编辑，不会发出 update-title", async () => {
    const TodoItem = (await import("../../src/components/TodoItem.vue")).default;
    const wrapper = mount(TodoItem, {
      props: { todo: createTodo({ id: 3, title: "done", completed: true }) },
    });

    expect(wrapper.find('button[title="置顶"]').exists()).toBe(false);
    expect(wrapper.find('button[title="取消置顶"]').exists()).toBe(false);

    const input = getTitleInput(wrapper);
    await input.setValue("changed");
    await input.trigger("blur");
    expect(wrapper.emitted("update-title")).toBeUndefined();
  });
});
