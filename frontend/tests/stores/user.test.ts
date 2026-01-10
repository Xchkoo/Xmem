import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

vi.mock("../../src/api/client", () => {
  return {
    default: {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      defaults: { baseURL: "/api" },
    },
  };
});

vi.mock("../../src/utils/crypto", () => {
  return {
    /**
     * 将密码 hash，用于登录/修改密码测试。
     */
    hashPassword: vi.fn(async (password: string) => `hashed:${password}`),
  };
});

/**
 * 清理 localStorage，避免测试间相互污染。
 */
const clearAuthStorage = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("quickInputText");
};

describe("useUserStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    clearAuthStorage();
    vi.clearAllMocks();
  });

  it("login 会保存 token，并拉取 profile", async () => {
    const api = (await import("../../src/api/client")).default as any;
    api.post.mockResolvedValue({ data: { access_token: "token-123" } });
    api.get.mockResolvedValue({ data: { id: 1, email: "a@b.com", user_name: "u" } });

    const { useUserStore } = await import("../../src/stores/user");
    const user = useUserStore();

    await user.login("a@b.com", "pw");

    expect(user.token).toBe("token-123");
    expect(localStorage.getItem("token")).toBe("token-123");
    expect(user.profile).toMatchObject({ id: 1, email: "a@b.com" });
    expect(api.post).toHaveBeenCalledWith("/auth/login", { email: "a@b.com", password: "hashed:pw" });
    expect(api.get).toHaveBeenCalledWith("/auth/me");
  });

  it("logout 会清理 token 与 profile，并清空数据缓存", async () => {
    const { useUserStore } = await import("../../src/stores/user");
    const { useDataStore } = await import("../../src/stores/data");
    const user = useUserStore();
    const data = useDataStore();

    data.notes = [{ id: 1, body_md: "x", created_at: "2026-01-01T00:00:00Z" }];
    user.token = "t";
    user.profile = { id: 1, email: "a@b.com", user_name: "u" };
    localStorage.setItem("token", "t");
    localStorage.setItem("quickInputText", "something");

    user.logout();

    expect(user.token).toBe("");
    expect(user.profile).toBeNull();
    expect(localStorage.getItem("token")).toBeNull();
    expect(localStorage.getItem("quickInputText")).toBeNull();
    expect(data.notes.length).toBe(0);
  });
});

