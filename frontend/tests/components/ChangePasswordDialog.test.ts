import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useUserStore } from "../../src/stores/user";
import { useToastStore } from "../../src/stores/toast";

/**
 * 填充修改密码表单并触发提交。
 */
const fillAndSubmit = async (wrapper: any, params: { oldPw: string; newPw: string; confirmPw: string }) => {
  await wrapper.get('input[placeholder="请输入原密码"]').setValue(params.oldPw);
  await wrapper.get('input[placeholder="请输入新密码"]').setValue(params.newPw);
  await wrapper.get('input[placeholder="请再次输入新密码"]').setValue(params.confirmPw);
  await wrapper.get("form").trigger("submit");
};

describe("ChangePasswordDialog", () => {
  beforeEach(() => {
    vi.resetModules();
    setActivePinia(createPinia());
  });

  it("两次密码不一致会提示错误且不调用 changePassword", async () => {
    const ChangePasswordDialog = (await import("../../src/components/ChangePasswordDialog.vue")).default;
    const user = useUserStore();
    const changeSpy = vi.spyOn(user, "changePassword").mockResolvedValue(undefined as any);

    const wrapper = mount(ChangePasswordDialog, {
      props: { visible: true },
      global: {
        stubs: { transition: false },
      },
    });

    await fillAndSubmit(wrapper, { oldPw: "o", newPw: "n1", confirmPw: "n2" });
    expect(wrapper.text()).toContain("两次输入的密码不一致");
    expect(changeSpy).not.toHaveBeenCalled();
  });

  it("提交成功会调用 changePassword、toast.success 并触发 saved", async () => {
    const ChangePasswordDialog = (await import("../../src/components/ChangePasswordDialog.vue")).default;
    const user = useUserStore();
    const toast = useToastStore();
    const changeSpy = vi.spyOn(user, "changePassword").mockResolvedValue(undefined as any);
    const toastSpy = vi.spyOn(toast, "success").mockImplementation(() => "id");

    const wrapper = mount(ChangePasswordDialog, {
      props: { visible: true },
      global: {
        stubs: { transition: false },
      },
    });

    await fillAndSubmit(wrapper, { oldPw: "old", newPw: "new", confirmPw: "new" });

    expect(changeSpy).toHaveBeenCalledWith("old", "new");
    expect(toastSpy).toHaveBeenCalledWith("密码修改成功");
    expect(wrapper.emitted("saved")).toBeTruthy();
  });

  it("提交失败会展示后端返回的错误信息", async () => {
    const ChangePasswordDialog = (await import("../../src/components/ChangePasswordDialog.vue")).default;
    const user = useUserStore();
    vi.spyOn(user, "changePassword").mockRejectedValue({
      response: { data: { detail: "旧密码错误" } },
    });

    const wrapper = mount(ChangePasswordDialog, {
      props: { visible: true },
      global: {
        stubs: { transition: false },
      },
    });

    await fillAndSubmit(wrapper, { oldPw: "old", newPw: "new", confirmPw: "new" });
    expect(wrapper.text()).toContain("旧密码错误");
    expect(wrapper.emitted("saved")).toBeFalsy();
  });
});

