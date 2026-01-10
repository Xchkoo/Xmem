import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { Todo } from "../../src/stores/data";

/**
 * 构造待办数据，便于覆盖组标题与组内子待办的交互分支。
 */
const createTodo = (overrides: Partial<Todo> = {}): Todo => {
  return {
    id: 1,
    title: "group",
    completed: false,
    is_pinned: false,
    group_id: null,
    group_items: [],
    created_at: "2026-01-10T00:00:00Z",
    ...overrides,
  };
};

/**
 * 获取 TodoGroup 内所有可编辑输入框（排除复选框），顺序与 DOM 一致。
 */
const getTextInputs = (wrapper: any) => {
  return wrapper
    .findAll("input")
    .filter((i: any) => (i.element as HTMLInputElement).type !== "checkbox");
};

describe("TodoGroup", () => {
  it("组标题：勾选、置顶、删除、添加子待办会发出事件", async () => {
    const TodoGroup = (await import("../../src/components/TodoGroup.vue")).default;
    const wrapper = mount(TodoGroup, {
      props: {
        todo: createTodo({
          id: 5,
          title: "g",
          group_items: [createTodo({ id: 50, title: "i", group_id: 5, created_at: "2026-01-10T00:00:00Z" })],
        }),
      },
    });

    await wrapper.get('input[type="checkbox"]').trigger("change");
    expect(wrapper.emitted("toggle")?.[0]).toEqual([5]);

    const pinBtn = wrapper.find('button[title="置顶"]');
    expect(pinBtn.exists()).toBe(true);
    await pinBtn.trigger("click");
    expect(wrapper.emitted("pin")?.[0]).toEqual([5]);

    const addBtn = wrapper.find('button[title="添加待办"]');
    expect(addBtn.exists()).toBe(true);
    await addBtn.trigger("click");
    expect(wrapper.emitted("add-item")?.[0]).toEqual([5]);

    const deleteBtn = wrapper.find('button[title="删除组"]');
    expect(deleteBtn.exists()).toBe(true);
    await deleteBtn.trigger("click");
    expect(wrapper.emitted("delete")?.[0]).toEqual([5]);
  });

  it("编辑组标题：blur/enter 会在内容变化时发出 update-title，esc 会回滚", async () => {
    const TodoGroup = (await import("../../src/components/TodoGroup.vue")).default;
    const wrapper = mount(TodoGroup, { props: { todo: createTodo({ id: 6, title: "old" }) } });

    const titleInput = getTextInputs(wrapper).at(0);
    expect(titleInput).toBeTruthy();

    await titleInput!.setValue("  new  ");
    await titleInput!.trigger("blur");
    expect(wrapper.emitted("update-title")?.[0]).toEqual([6, "new"]);

    await titleInput!.setValue("x");
    await titleInput!.trigger("keydown.enter");
    expect(wrapper.emitted("update-title")?.[1]).toEqual([6, "x"]);

    await titleInput!.setValue("should-cancel");
    await titleInput!.trigger("keydown.esc");
    expect((titleInput!.element as HTMLInputElement).value).toBe("old");
  });

  it("组内待办：勾选、删除、编辑会发出对应事件；回车会保存并创建新待办", async () => {
    const TodoGroup = (await import("../../src/components/TodoGroup.vue")).default;
    const wrapper = mount(TodoGroup, {
      props: {
        todo: createTodo({
          id: 7,
          group_items: [
            createTodo({ id: 71, title: "a", group_id: 7, created_at: "2026-01-10T00:00:00Z" }),
          ],
        }),
      },
    });

    await wrapper.findAll('input[type="checkbox"]').at(1)!.trigger("change");
    expect(wrapper.emitted("toggle-item")?.[0]).toEqual([71]);

    const deleteItemBtn = wrapper.find('button[title="删除待办"]');
    expect(deleteItemBtn.exists()).toBe(true);
    await deleteItemBtn.trigger("click");
    expect(wrapper.emitted("delete-item")?.[0]).toEqual([71]);

    const itemInput = getTextInputs(wrapper).at(1);
    expect(itemInput).toBeTruthy();

    await itemInput!.setValue("  updated  ");
    await itemInput!.trigger("blur");
    expect(wrapper.emitted("update-item-title")?.[0]).toEqual([71, "updated"]);

    await itemInput!.setValue("enter-save");
    await itemInput!.trigger("keydown.enter");
    expect(wrapper.emitted("update-item-title")?.[1]).toEqual([71, "enter-save"]);
    expect(wrapper.emitted("add-item")?.[0]).toEqual([7]);
  });
});
