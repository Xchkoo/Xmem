import { mount } from "@vue/test-utils";
import { describe, expect, it, vi, afterEach } from "vitest";
import { defineComponent, nextTick } from "vue";
import NoteCardContent from "../../src/components/NoteCardContent.vue";
import type { Note } from "../../src/stores/data";

vi.mock("md-editor-v3", () => {
  return {
    MdPreview: defineComponent({
      name: "MdPreview",
      props: {
        editorId: { type: String, required: true },
        modelValue: { type: String, required: true },
      },
      template: `<div class="md-preview-stub" v-html="modelValue"></div>`,
    }),
  };
});

/**
 * 构造一个最小的 Note 供 NoteCardContent 测试。
 */
const createNote = (overrides: Partial<Note> = {}): Note => {
  return {
    id: 1,
    body_md: "hello world",
    created_at: "2026-01-10T06:30:00Z",
    is_pinned: false,
    ...overrides,
  };
};

/**
 * 安装可控的 ResizeObserver mock，用于触发折叠逻辑。
 */
const installResizeObserverMock = () => {
  const original = window.ResizeObserver;
  let lastInstance: any | null = null;

  class MockResizeObserver {
    private readonly cb: any;
    private target: Element | null = null;

    constructor(cb: any) {
      this.cb = cb;
      lastInstance = this;
    }

    observe(target: Element) {
      this.target = target;
    }

    unobserve() {}

    disconnect() {}

    trigger(scrollHeight: number) {
      if (!this.target) return;
      Object.defineProperty(this.target, "scrollHeight", {
        value: scrollHeight,
        configurable: true,
      });
      this.cb([{ target: this.target }], this);
    }
  }

  (window as any).ResizeObserver = MockResizeObserver;

  return {
    getLastInstance: () => lastInstance as InstanceType<typeof MockResizeObserver> | null,
    restore: () => {
      window.ResizeObserver = original;
    },
  };
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("NoteCardContent", () => {
  it("点击操作按钮会触发 copy/delete/pin 事件", async () => {
    const wrapper = mount(NoteCardContent, {
      props: { note: createNote() },
      global: {
        directives: {
          secureDisplay: {
            mounted() {},
            updated() {},
            unmounted() {},
          },
        },
      },
    });

    await wrapper.get('button[title="置顶"]').trigger("click");
    await wrapper.get('button[title="复制文本"]').trigger("click");
    await wrapper.get('button[title="删除笔记"]').trigger("click");

    expect(wrapper.emitted("pin")).toBeTruthy();
    expect(wrapper.emitted("copy")).toBeTruthy();
    expect(wrapper.emitted("delete")).toBeTruthy();
  });

  it("双击内容区域会触发 edit 事件", async () => {
    const wrapper = mount(NoteCardContent, {
      props: { note: createNote() },
      global: {
        directives: {
          secureDisplay: {
            mounted() {},
            updated() {},
            unmounted() {},
          },
        },
      },
    });

    await wrapper.get(".note-content").trigger("dblclick");
    expect(wrapper.emitted("edit")).toBeTruthy();
  });

  it("带 searchQuery 时会高亮匹配文本", () => {
    const wrapper = mount(NoteCardContent, {
      props: { note: createNote({ body_md: "foo bar baz" }), searchQuery: "bar" },
      global: {
        directives: {
          secureDisplay: {
            mounted() {},
            updated() {},
            unmounted() {},
          },
        },
      },
    });

    expect(wrapper.find("mark").exists()).toBe(true);
    expect(wrapper.find("mark").text()).toBe("bar");
  });

  it("内容高度超过阈值时会显示折叠提示", async () => {
    const ro = installResizeObserverMock();

    const wrapper = mount(NoteCardContent, {
      props: { note: createNote({ body_md: "x".repeat(500) }) },
      global: {
        directives: {
          secureDisplay: {
            mounted() {},
            updated() {},
            unmounted() {},
          },
        },
      },
    });

    ro.getLastInstance()?.trigger(260);
    await nextTick();
    expect(wrapper.text()).toContain("点击查看完整内容");

    ro.restore();
  });
});
