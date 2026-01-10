import { afterEach, describe, expect, it, vi } from "vitest";

describe("crypto/hashPassword", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("会调用 crypto.subtle.digest 并返回 hex 字符串", async () => {
    const digest = vi.fn(async (_algo: string, _data: ArrayBuffer | ArrayBufferView) => {
      return new Uint8Array([0, 1, 2, 255]).buffer;
    });

    vi.stubGlobal("crypto", { subtle: { digest } } as any);

    const { hashPassword } = await import("../../src/utils/crypto");
    const result = await hashPassword("pw");

    expect(digest).toHaveBeenCalledTimes(1);
    expect(digest.mock.calls[0]?.[0]).toBe("SHA-256");
    expect(result).toBe("000102ff");
  });

  it("会把输入按 UTF-8 编码后参与 digest", async () => {
    const digest = vi.fn(async (_algo: string, data: any) => {
      const bytes = data instanceof ArrayBuffer ? new Uint8Array(data) : new Uint8Array(data.buffer);
      const decoded = new TextDecoder().decode(bytes);
      expect(decoded).toBe("你好");
      return new Uint8Array([16]).buffer;
    });

    vi.stubGlobal("crypto", { subtle: { digest } } as any);

    const { hashPassword } = await import("../../src/utils/crypto");
    const result = await hashPassword("你好");

    expect(result).toBe("10");
  });
});

