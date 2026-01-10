import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { defineComponent } from "vue";
import { useDataStore, type Todo } from "../../src/stores/data";

const TodoInputStub = defineComponent({
  name: "TodoInput",
  template: `<div data-test="todo-input"></div>`,
});

const TodoListStub = defineComponent({
  name: "TodoList",
  props: ["todos", "showCompleted"],
  emits: [
    "toggle",
    "update-title",
    "delete",
    "delete-group",
    "delete-item",
    "pin",
    "add-group-item",
    "update-item-title",
    "toggle-item",
  ],
  template: `
    <div>
      <div data-test="order">{{ (todos || []).map(t => t.id).join(',') }}</div>
      <button data-test="toggle" @click="$emit('toggle', 1)">toggle</button>
      <button data-test="update-title" @click="$emit('update-title', 1, 't')">update-title</button>
      <button data-test="delete" @click="$emit('delete', 1)">delete</button>
      <button data-test="delete-group" @click="$emit('delete-group', 2)">delete-group</button>
      <button data-test="delete-item" @click="$emit('delete-item', 3)">delete-item</button>
      <button data-test="pin" @click="$emit('pin', 1)">pin</button>
      <button data-test="add-group-item" @click="$emit('add-group-item', 2)">add-group-item</button>
      <button data-test="update-item-title" @click="$emit('update-item-title', 3, 'it')">update-item-title</button>
      <button data-test="toggle-item" @click="$emit('toggle-item', 3)">toggle-item</button>
    </div>
  `,
});

/**
 * 构造待办数据，便于覆盖排序与事件参数。
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

describe("TodosView", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("会按置顶优先、创建时间倒序传递给 TodoList", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div>home</div>" } }],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    data.todos = [
      createTodo({ id: 1, is_pinned: false, created_at: "2026-01-09T00:00:00Z" }),
      createTodo({ id: 2, is_pinned: true, created_at: "2026-01-01T00:00:00Z" }),
      createTodo({ id: 3, is_pinned: false, created_at: "2026-01-10T00:00:00Z" }),
    ];

    const TodosView = (await import("../../src/views/TodosView.vue")).default;
    const wrapper = mount(TodosView, {
      global: { plugins: [pinia, router], stubs: { TodoInput: TodoInputStub, TodoList: TodoListStub } },
    });

    expect(wrapper.get('[data-test="order"]').text()).toBe("2,3,1");
  });

  it("TodoList 事件会调用对应的 store actions", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div>home</div>" } }],
    });
    await router.push("/");
    await router.isReady();

    const data = useDataStore();
    const toggleSpy = vi.spyOn(data, "toggleTodo").mockResolvedValue({} as any);
    const updateSpy = vi.spyOn(data, "updateTodo").mockResolvedValue({} as any);
    const removeSpy = vi.spyOn(data, "removeTodo").mockResolvedValue(undefined as any);
    const pinSpy = vi.spyOn(data, "togglePinTodo").mockResolvedValue({} as any);
    const addSpy = vi.spyOn(data, "addTodo").mockResolvedValue({} as any);

    const TodosView = (await import("../../src/views/TodosView.vue")).default;
    const wrapper = mount(TodosView, {
      global: { plugins: [pinia, router], stubs: { TodoInput: TodoInputStub, TodoList: TodoListStub } },
    });

    await wrapper.get('[data-test="toggle"]').trigger("click");
    expect(toggleSpy).toHaveBeenCalledWith(1);

    await wrapper.get('[data-test="update-title"]').trigger("click");
    expect(updateSpy).toHaveBeenCalledWith(1, { title: "t" });

    await wrapper.get('[data-test="delete"]').trigger("click");
    expect(removeSpy).toHaveBeenCalledWith(1);

    await wrapper.get('[data-test="delete-group"]').trigger("click");
    expect(removeSpy).toHaveBeenCalledWith(2);

    await wrapper.get('[data-test="delete-item"]').trigger("click");
    expect(removeSpy).toHaveBeenCalledWith(3);

    await wrapper.get('[data-test="pin"]').trigger("click");
    expect(pinSpy).toHaveBeenCalledWith(1);

    await wrapper.get('[data-test="add-group-item"]').trigger("click");
    expect(addSpy).toHaveBeenCalledWith("新建待办", 2);

    await wrapper.get('[data-test="update-item-title"]').trigger("click");
    expect(updateSpy).toHaveBeenCalledWith(3, { title: "it" });

    await wrapper.get('[data-test="toggle-item"]').trigger("click");
    expect(toggleSpy).toHaveBeenCalledWith(3);
  });

  it("返回按钮会调用 router.back", async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div>home</div>" } }],
    });
    await router.push("/");
    await router.isReady();

    const backSpy = vi.spyOn(router, "back");
    const TodosView = (await import("../../src/views/TodosView.vue")).default;
    const wrapper = mount(TodosView, {
      global: { plugins: [pinia, router], stubs: { TodoInput: TodoInputStub, TodoList: TodoListStub } },
    });

    const backBtn = wrapper.findAll("header button").find((b) => b.text().includes("返回"));
    expect(backBtn).toBeTruthy();
    await backBtn!.trigger("click");
    expect(backSpy).toHaveBeenCalledTimes(1);
  });
});

