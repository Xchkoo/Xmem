import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { vSecureDisplay } from "../../src/directives/secureDisplay";

const replaceImagesWithSecureUrlsMock = vi.hoisted(() => vi.fn());
const isSecureResourceMock = vi.hoisted(() => vi.fn());
const handleSecureDownloadMock = vi.hoisted(() => vi.fn(async () => {}));

vi.mock("../../src/utils/secureImages", () => ({ replaceImagesWithSecureUrls: replaceImagesWithSecureUrlsMock }));
vi.mock("../../src/utils/secureDownload", () => ({
  isSecureResource: isSecureResourceMock,
  handleSecureDownload: handleSecureDownloadMock,
}));

describe("vSecureDisplay", () => {
  it("会防抖触发图片替换，并拦截受保护链接下载", async () => {
    vi.useFakeTimers();
    isSecureResourceMock.mockReturnValue(true);

    const Comp = defineComponent({
      template: `<div v-secure-display><a href="/api/notes/files/a.txt">a</a></div>`,
    });

    const wrapper = mount(Comp, {
      global: {
        directives: { "secure-display": vSecureDisplay },
      },
    });

    expect(replaceImagesWithSecureUrlsMock).not.toHaveBeenCalled();
    vi.advanceTimersByTime(300);
    expect(replaceImagesWithSecureUrlsMock).toHaveBeenCalledTimes(1);

    const link = wrapper.get("a").element as HTMLAnchorElement;
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    link.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    expect(handleSecureDownloadMock).toHaveBeenCalledWith(link.href);

    wrapper.unmount();
    vi.useRealTimers();
  });
});

