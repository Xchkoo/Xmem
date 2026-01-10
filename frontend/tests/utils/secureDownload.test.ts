import { beforeEach, describe, expect, it, vi } from "vitest";

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  defaults: { baseURL: "/api" },
}));

const toastMock = vi.hoisted(() => ({
  info: vi.fn(),
  success: vi.fn(),
  error: vi.fn(),
}));

vi.mock("../../src/api/client", () => ({ default: apiMock }));
vi.mock("../../src/stores/toast", () => ({ useToastStore: () => toastMock }));

describe("secureDownload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMock.defaults.baseURL = "/api";
    if (!(URL as any).createObjectURL) {
      Object.defineProperty(URL, "createObjectURL", {
        value: vi.fn(() => "blob:mock"),
        writable: true,
        configurable: true,
      });
    }
    if (!(URL as any).revokeObjectURL) {
      Object.defineProperty(URL, "revokeObjectURL", {
        value: vi.fn(() => {}),
        writable: true,
        configurable: true,
      });
    }
  });

  it("isSecureResource 支持相对路径与同源绝对路径", async () => {
    const { isSecureResource } = await import("../../src/utils/secureDownload");

    expect(isSecureResource("/api/notes/files/x")).toBe(true);
    expect(isSecureResource("/notes/files/x")).toBe(true);
    expect(isSecureResource("/notes/x")).toBe(false);
    expect(isSecureResource("")).toBe(false);

    const absolute = `${window.location.origin}/api/notes/files/a.png`;
    expect(isSecureResource(absolute)).toBe(true);
  });

  it("isSecureResource 支持 baseURL 为绝对地址的情况", async () => {
    const { isSecureResource } = await import("../../src/utils/secureDownload");
    apiMock.defaults.baseURL = "https://api.example.com";

    expect(isSecureResource("https://api.example.com/notes/files/a")).toBe(true);
    expect(isSecureResource("https://api.example.com/api/notes/files/a")).toBe(true);
    expect(isSecureResource("https://evil.example.com/notes/files/a")).toBe(false);
  });

  it("handleSecureDownload 遇到非内部资源会直接 window.open", async () => {
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null as any);
    const { handleSecureDownload } = await import("../../src/utils/secureDownload");

    await handleSecureDownload("https://example.com/a.txt");

    expect(openSpy).toHaveBeenCalledWith("https://example.com/a.txt", "_blank");
    expect(apiMock.get).not.toHaveBeenCalled();
  });

  it("handleSecureDownload 会规范化请求路径并触发下载", async () => {
    const { handleSecureDownload } = await import("../../src/utils/secureDownload");

    const createObjectUrlSpy = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock");
    const revokeSpy = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    apiMock.get.mockResolvedValue({
      data: new Blob(["x"], { type: "text/plain" }),
      headers: { "content-disposition": 'attachment; filename="a.txt"' },
    });

    await handleSecureDownload("/api/notes/files/a.txt");

    expect(toastMock.info).toHaveBeenCalled();
    expect(apiMock.get).toHaveBeenCalledWith("/notes/files/a.txt", { responseType: "blob" });
    expect(createObjectUrlSpy).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(revokeSpy).toHaveBeenCalledWith("blob:mock");
    expect(toastMock.success).toHaveBeenCalled();
  });

  it("handleSecureDownload 下载失败会提示错误", async () => {
    const { handleSecureDownload } = await import("../../src/utils/secureDownload");
    apiMock.get.mockRejectedValue(new Error("boom"));

    await handleSecureDownload("/api/notes/files/a.txt");
    expect(toastMock.error).toHaveBeenCalled();
  });
});
