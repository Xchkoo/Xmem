import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const stubSfc = (name: string) => ({ default: { name, template: `<div>${name}</div>` } });

describe("router/index", () => {
  beforeEach(() => {
    vi.resetModules();
    (window as any).scrollTo = vi.fn();
    localStorage.clear();
    setActivePinia(createPinia());
  });

  it("未登录访问非 Auth 路由会跳转 login 并携带 redirect", async () => {
    vi.mock("../../src/views/HomeView.vue", () => stubSfc("HomeView"));
    vi.mock("../../src/views/NotesView.vue", () => stubSfc("NotesView"));
    vi.mock("../../src/views/LedgersView.vue", () => stubSfc("LedgersView"));
    vi.mock("../../src/views/TodosView.vue", () => stubSfc("TodosView"));
    vi.mock("../../src/views/LedgerStatisticsView.vue", () => stubSfc("LedgerStatisticsView"));
    vi.mock("../../src/views/NoteEditor.vue", () => stubSfc("NoteEditor"));
    vi.mock("../../src/views/NoteView.vue", () => stubSfc("NoteView"));
    vi.mock("../../src/views/LedgerView.vue", () => stubSfc("LedgerView"));
    vi.mock("../../src/views/NotFound.vue", () => stubSfc("NotFound"));
    vi.mock("../../src/views/ServerError.vue", () => stubSfc("ServerError"));
    vi.mock("../../src/components/Auth.vue", () => stubSfc("Auth"));

    const router = (await import("../../src/router")).default;
    const { useUserStore } = await import("../../src/stores/user");
    const { useUiStore } = await import("../../src/stores/ui");
    const user = useUserStore();
    const ui = useUiStore();

    user.token = "";
    const startSpy = vi.spyOn(ui, "startRouteTransition");

    await router.push("/notes");
    await router.isReady();

    expect(router.currentRoute.value.name).toBe("login");
    expect(router.currentRoute.value.query.redirect).toBe("/notes");
    expect(startSpy).toHaveBeenCalledTimes(1);
  });

  it("已登录访问 login/register 会跳转 home", async () => {
    vi.mock("../../src/views/HomeView.vue", () => stubSfc("HomeView"));
    vi.mock("../../src/views/NotesView.vue", () => stubSfc("NotesView"));
    vi.mock("../../src/views/LedgersView.vue", () => stubSfc("LedgersView"));
    vi.mock("../../src/views/TodosView.vue", () => stubSfc("TodosView"));
    vi.mock("../../src/views/LedgerStatisticsView.vue", () => stubSfc("LedgerStatisticsView"));
    vi.mock("../../src/views/NoteEditor.vue", () => stubSfc("NoteEditor"));
    vi.mock("../../src/views/NoteView.vue", () => stubSfc("NoteView"));
    vi.mock("../../src/views/LedgerView.vue", () => stubSfc("LedgerView"));
    vi.mock("../../src/views/NotFound.vue", () => stubSfc("NotFound"));
    vi.mock("../../src/views/ServerError.vue", () => stubSfc("ServerError"));
    vi.mock("../../src/components/Auth.vue", () => stubSfc("Auth"));

    const router = (await import("../../src/router")).default;
    const { useUserStore } = await import("../../src/stores/user");
    const user = useUserStore();
    user.token = "t";

    await router.push({ name: "login" });
    await router.isReady();
    expect(router.currentRoute.value.name).toBe("home");

    await router.push({ name: "register" });
    await router.isReady();
    expect(router.currentRoute.value.name).toBe("home");
  });

  it("正常导航会触发 start/finishRouteTransition", async () => {
    vi.mock("../../src/views/HomeView.vue", () => stubSfc("HomeView"));
    vi.mock("../../src/views/NotesView.vue", () => stubSfc("NotesView"));
    vi.mock("../../src/views/LedgersView.vue", () => stubSfc("LedgersView"));
    vi.mock("../../src/views/TodosView.vue", () => stubSfc("TodosView"));
    vi.mock("../../src/views/LedgerStatisticsView.vue", () => stubSfc("LedgerStatisticsView"));
    vi.mock("../../src/views/NoteEditor.vue", () => stubSfc("NoteEditor"));
    vi.mock("../../src/views/NoteView.vue", () => stubSfc("NoteView"));
    vi.mock("../../src/views/LedgerView.vue", () => stubSfc("LedgerView"));
    vi.mock("../../src/views/NotFound.vue", () => stubSfc("NotFound"));
    vi.mock("../../src/views/ServerError.vue", () => stubSfc("ServerError"));
    vi.mock("../../src/components/Auth.vue", () => stubSfc("Auth"));

    const router = (await import("../../src/router")).default;
    const { useUserStore } = await import("../../src/stores/user");
    const { useUiStore } = await import("../../src/stores/ui");
    const user = useUserStore();
    const ui = useUiStore();
    user.token = "t";

    const startSpy = vi.spyOn(ui, "startRouteTransition");
    const finishSpy = vi.spyOn(ui, "finishRouteTransition");

    await router.push({ name: "notes" });
    await router.isReady();

    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(finishSpy).toHaveBeenCalledTimes(1);
  });

  it("scrollBehavior 对 home 和 savedPosition 生效", async () => {
    vi.mock("../../src/views/HomeView.vue", () => stubSfc("HomeView"));
    vi.mock("../../src/views/NotesView.vue", () => stubSfc("NotesView"));
    vi.mock("../../src/views/LedgersView.vue", () => stubSfc("LedgersView"));
    vi.mock("../../src/views/TodosView.vue", () => stubSfc("TodosView"));
    vi.mock("../../src/views/LedgerStatisticsView.vue", () => stubSfc("LedgerStatisticsView"));
    vi.mock("../../src/views/NoteEditor.vue", () => stubSfc("NoteEditor"));
    vi.mock("../../src/views/NoteView.vue", () => stubSfc("NoteView"));
    vi.mock("../../src/views/LedgerView.vue", () => stubSfc("LedgerView"));
    vi.mock("../../src/views/NotFound.vue", () => stubSfc("NotFound"));
    vi.mock("../../src/views/ServerError.vue", () => stubSfc("ServerError"));
    vi.mock("../../src/components/Auth.vue", () => stubSfc("Auth"));

    const router = (await import("../../src/router")).default as any;
    const scrollBehavior = router.options.scrollBehavior as any;

    expect(scrollBehavior({ name: "home" }, {}, null)).toEqual({ left: 0, top: 0 });
    expect(scrollBehavior({ name: "notes" }, {}, { left: 1, top: 2 })).toEqual({ left: 1, top: 2 });
    expect(scrollBehavior({ name: "notes" }, {}, null)).toEqual({ left: 0, top: 0 });
  });
});

