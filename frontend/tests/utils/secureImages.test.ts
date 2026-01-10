import { beforeEach, describe, expect, it, vi } from "vitest";

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  defaults: { baseURL: "/api" },
}));

vi.mock("../../src/api/client", () => ({ default: apiMock }));

describe("replaceImagesWithSecureUrls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    if (!(URL as any).createObjectURL) {
      Object.defineProperty(URL, "createObjectURL", {
        value: vi.fn(() => "blob:img"),
        writable: true,
        configurable: true,
      });
    }
  });

  it("会将 /notes/files/ 图片替换为 blob URL，并设置 dataset 状态", async () => {
    const { replaceImagesWithSecureUrls } = await import("../../src/utils/secureImages");

    const createObjectUrlSpy = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:img");
    apiMock.get.mockResolvedValue({ data: new Blob(["x"], { type: "image/png" }) });

    const container = document.createElement("div");
    const secureImg = document.createElement("img");
    secureImg.setAttribute("src", "/api/notes/files/a.png");
    const normalImg = document.createElement("img");
    normalImg.setAttribute("src", "/public/a.png");
    const blobImg = document.createElement("img");
    blobImg.setAttribute("src", "blob:exists");

    container.appendChild(secureImg);
    container.appendChild(normalImg);
    container.appendChild(blobImg);

    await replaceImagesWithSecureUrls(container);
    await new Promise((r) => setTimeout(r, 0));

    expect(apiMock.get).toHaveBeenCalledWith("/notes/files/a.png", { responseType: "blob" });
    expect(createObjectUrlSpy).toHaveBeenCalled();
    expect(secureImg.src).toContain("blob:img");
    expect(secureImg.dataset.loaded).toBe("true");
    expect(secureImg.dataset.loading).toBe("false");
  });
});
