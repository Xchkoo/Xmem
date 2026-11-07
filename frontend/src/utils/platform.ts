import { Capacitor } from "@capacitor/core";
import { computed, onUnmounted, ref } from "vue";

/** 是否运行在 Capacitor 的 Android 壳里。 */
export const isNativeAndroid = (): boolean => {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "android";
};

/**
 * 是否使用移动端外壳（底部导航栏）。
 *
 * 判定：原生 Android，或视口宽度 ≤ 640px（手机浏览器 / WebView）。
 * 桌面 Web 保持原有悬浮球布局不变。
 */
export const MOBILE_SHELL_QUERY = "(max-width: 640px)";

export function useMobileShell() {
  const supported =
    typeof window !== "undefined" && typeof window.matchMedia === "function";
  const matches = ref(
    supported ? window.matchMedia(MOBILE_SHELL_QUERY).matches : false,
  );

  if (supported) {
    const mql = window.matchMedia(MOBILE_SHELL_QUERY);
    const handler = (event: MediaQueryListEvent) => {
      matches.value = event.matches;
    };
    mql.addEventListener?.("change", handler);
    onUnmounted(() => mql.removeEventListener?.("change", handler));
  }

  return computed(() => isNativeAndroid() || matches.value);
}
