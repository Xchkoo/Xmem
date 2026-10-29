import { Capacitor, registerPlugin } from "@capacitor/core";

/**
 * 与原生「截屏记账」能力的桥。
 *
 * 只在 Android 原生壳里生效；Web / 开发环境下所有方法都是 no-op，
 * 因此调用方不需要到处判断平台。
 */
export interface CaptureState {
  hasSession: boolean;
  previewEnabled: boolean;
  baseUrl: string;
}

interface XmemCapturePluginApi {
  setSession(options: { token: string; baseUrl: string }): Promise<void>;
  clearSession(): Promise<void>;
  setPreviewEnabled(options: { enabled: boolean }): Promise<void>;
  getState(): Promise<CaptureState>;
  consumePendingLedger(): Promise<{ ledgerId: number }>;
}

const plugin = registerPlugin<XmemCapturePluginApi>("XmemCapture");

/** 当前环境是否支持快捷开关截屏记账（仅 Android 原生）。 */
export const isNativeCaptureAvailable = (): boolean => {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "android";
};

export const nativeCapture = {
  /** 登录后把 token 与 API 地址交给原生，供磁贴/分享入口使用。 */
  async setSession(token: string, baseUrl: string): Promise<void> {
    if (!isNativeCaptureAvailable() || !token) return;
    try {
      await plugin.setSession({ token, baseUrl });
    } catch {
      // 旧版本 APK 没有该插件，静默忽略
    }
  },

  /** 退出登录时清空原生凭证，避免磁贴用旧 token 上传。 */
  async clearSession(): Promise<void> {
    if (!isNativeCaptureAvailable()) return;
    try {
      await plugin.clearSession();
    } catch {
      // ignore
    }
  },

  async setPreviewEnabled(enabled: boolean): Promise<void> {
    if (!isNativeCaptureAvailable()) return;
    try {
      await plugin.setPreviewEnabled({ enabled });
    } catch {
      // ignore
    }
  },

  async getState(): Promise<CaptureState | null> {
    if (!isNativeCaptureAvailable()) return null;
    try {
      return await plugin.getState();
    } catch {
      return null;
    }
  },

  /** 读取「通知点开后要跳到哪笔账」，读取后原生侧即清空。 */
  async consumePendingLedger(): Promise<number> {
    if (!isNativeCaptureAvailable()) return 0;
    try {
      const { ledgerId } = await plugin.consumePendingLedger();
      return Number(ledgerId) || 0;
    } catch {
      return 0;
    }
  },
};
