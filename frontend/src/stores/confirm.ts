import { defineStore } from "pinia";

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: "danger" | "warning" | "info";
}

export interface ConfirmState extends ConfirmOptions {
  visible: boolean;
  resolve?: (value: boolean) => void;
}

export const useConfirmStore = defineStore("confirm", {
  state: (): ConfirmState => ({
    visible: false,
    message: "",
    title: "确认",
    confirmText: "确认",
    cancelText: "取消",
    type: "danger",
  }),

  actions: {
    show(options: ConfirmOptions): Promise<boolean> {
      return new Promise((resolve) => {
        this.title = options.title || "确认";
        this.message = options.message;
        this.confirmText = options.confirmText || "确认";
        this.cancelText = options.cancelText || "取消";
        this.type = options.type || "danger";
        this.visible = true;
        this.resolve = resolve;
      });
    },

    confirm() {
      if (this.resolve) {
        this.resolve(true);
        this.resolve = undefined;
      }
      this.visible = false;
    },

    cancel() {
      if (this.resolve) {
        this.resolve(false);
        this.resolve = undefined;
      }
      this.visible = false;
    },
  },
});

