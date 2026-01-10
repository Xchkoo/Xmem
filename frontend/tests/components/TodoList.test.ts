import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent } from "vue";
import type { Todo } from "../../src/stores/data";

/**
 * 构造待办数据，便于覆盖组/单项、已完成/未完成的渲染分支。
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

const TodoItemStub = defineComponent({
  name: "TodoItem",
  props: ["todo"],
  emits: ["toggle", "update-title", "delete", "pin"],
  template: `
    <div data-test="todo-item">
      <button data-test="toggle" @click="$emit('toggle', todo.id)">toggle</button>
      <button data-test="update-title" @click="$emit('update-title', todo.id, 't')">update</button>
      <button data-test="delete" @click="$emit('delete', todo.id)">delete</button>
      <button data-test="pin" @click="$emit('pin', todo.id)">pin</button>
    </div>
  `,
});

const TodoGroupStub = defineComponent({
  name: "TodoGroup",
  props: ["todo"],
  emits: ["toggle", "update-title", "delete", "pin", "add-item", "update-item-title", "toggle-item", "delete-item"],
  template: `
    <div data-test="todo-group">
      <button data-test="toggle" @click="$emit('toggle', todo.id)">toggle</button>
      <button data-test="update-title" @click="$emit('update-title', todo.id, 'g')">update</button>
      <button data-test="delete" @click="$emit('delete', todo.id)">delete</button>
      <button data-test="pin" @click="$emit('pin', todo.id)">pin</button>
      <button data-test="add-item" @click="$emit('add-item', todo.id)">add-item</button>
      <button data-test="update-item-title" @click="$emit('update-item-title', 99, 'i')">update-item</button>
      <button data-test="toggle-item" @click="$emit('toggle-item', 99)">toggle-item</button>
      <button data-test="delete-item" @click="$emit('delete-item', 99)">delete-item</button>
    </div>
  `,
});

describe("TodoList", () => {
  it("空列表会显示空状态", async () => {
    const TodoList = (await import("../../src/components/TodoList.vue")).default;
    const wrapper = mount(TodoList, {
      props: { todos: [] },
      global: { stubs: { TodoItem: TodoItemStub, TodoGroup: TodoGroupStub, TransitionGroup: false } },
    });

    expect(wrapper.text()).toContain("暂无待办事项");
  });

  it("会按 completed 分区渲染，并按子组件事件向上转发", async () => {
    const TodoList = (await import("../../src/components/TodoList.vue")).default;
    const todos: Todo[] = [
      createTodo({
        id: 1,
        title: "group",
        completed: false,
        group_items: [createTodo({ id: 10, group_id: 1, title: "i", created_at: "2026-01-10T00:00:00Z" })],
      }),
      createTodo({ id: 2, title: "single", completed: false }),
      createTodo({ id: 3, title: "done", completed: true }),
    ];

    const wrapper = mount(TodoList, {
      props: { todos, showCompleted: true, compact: false },
      global: { stubs: { TodoItem: TodoItemStub, TodoGroup: TodoGroupStub, TransitionGroup: false } },
    });

    expect(wrapper.text()).toContain("未完成");
    expect(wrapper.text()).toContain("完成");

    await wrapper.get('[data-test="todo-group"] [data-test="toggle"]').trigger("click");
    expect(wrapper.emitted("toggle")?.[0]).toEqual([1]);

    await wrapper.get('[data-test="todo-item"] [data-test="update-title"]').trigger("click");
    expect(wrapper.emitted("update-title")?.[0]).toEqual([2, "t"]);

    await wrapper.get('[data-test="todo-group"] [data-test="delete"]').trigger("click");
    expect(wrapper.emitted("delete-group")?.[0]).toEqual([1]);

    await wrapper.get('[data-test="todo-item"] [data-test="delete"]').trigger("click");
    expect(wrapper.emitted("delete")?.[0]).toEqual([2]);

    await wrapper.get('[data-test="todo-item"] [data-test="pin"]').trigger("click");
    expect(wrapper.emitted("pin")?.[0]).toEqual([2]);

    await wrapper.get('[data-test="todo-group"] [data-test="add-item"]').trigger("click");
    expect(wrapper.emitted("add-group-item")?.[0]).toEqual([1]);

    await wrapper.get('[data-test="todo-group"] [data-test="update-item-title"]').trigger("click");
    expect(wrapper.emitted("update-item-title")?.[0]).toEqual([99, "i"]);

    await wrapper.get('[data-test="todo-group"] [data-test="toggle-item"]').trigger("click");
    expect(wrapper.emitted("toggle-item")?.[0]).toEqual([99]);

    await wrapper.get('[data-test="todo-group"] [data-test="delete-item"]').trigger("click");
    expect(wrapper.emitted("delete-item")?.[0]).toEqual([99]);
  });

  it("showCompleted=false 时不显示完成分区", async () => {
    const TodoList = (await import("../../src/components/TodoList.vue")).default;
    const wrapper = mount(TodoList, {
      props: { todos: [createTodo({ id: 1, completed: true })], showCompleted: false, compact: false },
      global: { stubs: { TodoItem: TodoItemStub, TodoGroup: TodoGroupStub, TransitionGroup: false } },
    });

    expect(wrapper.text()).not.toContain("完成");
  });
});

