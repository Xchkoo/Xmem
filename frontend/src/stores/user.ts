import { defineStore } from "pinia";
import api from "../api/client";
import { useDataStore } from "./data";

const writeCapacitorPrefs = async (key: string, value: string) => {
  try {
    const { Preferences } = await import("@capacitor/preferences");
    if (value) {
      await Preferences.set({ key, value });
    } else {
      await Preferences.remove({ key });
    }
  } catch {
    // Not running in Capacitor environment, ignore
  }
};

interface UserProfile {
  id: number;
  email: string;
  user_name: string | null;
}

export const useUserStore = defineStore("user", {
  state: () => ({
    token: localStorage.getItem("token") || "",
    profile: null as UserProfile | null,
    loading: false
  }),
  actions: {
    /**
     * 校验当前登录/注册/改密操作是否处于安全传输环境（本地开发环境除外）。
     *
     * - 浏览器环境：页面本身必须是 https
     * - Electron 环境：页面可能是 file://，此时要求 API baseURL 必须是 https（或本地开发）
     */
    assertSecureTransport() {
      if (typeof window === "undefined") return;
      const location = window.location;
      const { protocol, hostname } = location;
      const isLocalHost =
        hostname === "localhost" ||
        hostname === "127.0.0.1" ||
        hostname === "[::1]" ||
        hostname === "";

      const isCapacitor =
        protocol === "capacitor:" ||
        protocol === "https:" && hostname === "localhost" && (window as any).Capacitor !== undefined;

      const apiBaseURL = (api.defaults.baseURL || "").toString();
      const isApiHttps = apiBaseURL.startsWith("https://");
      const isApiLocal =
        apiBaseURL.startsWith("http://localhost") ||
        apiBaseURL.startsWith("http://127.0.0.1") ||
        apiBaseURL.startsWith("http://[::1]");

      if (protocol === "https:" || isLocalHost || isCapacitor) return;

      if (protocol === "file:" && (isApiHttps || isApiLocal)) return;

      if (protocol !== "https:" && !isLocalHost) {
        throw new Error("为保障账号安全，登录/注册/改密仅允许在 HTTPS 环境下进行");
      }
    },
    /**
     * 清理与当前登录态相关的前端缓存，避免切换账号时短暂展示旧数据。
     */
    clearClientCache() {
      const dataStore = useDataStore();
      dataStore.reset();
      localStorage.removeItem("quickInputText");
    },
    async login(email: string, password: string) {
      this.loading = true;
      try {
        this.assertSecureTransport();
        const { data } = await api.post("/auth/login", { email, password });
        this.token = data.access_token;
        localStorage.setItem("token", data.access_token);
        writeCapacitorPrefs("token", data.access_token);
        writeCapacitorPrefs("baseUrl", (api.defaults.baseURL || "").toString());
        await this.fetchProfile();
      } finally {
        this.loading = false;
      }
    },
    async register(email: string, password: string, user_name?: string) {
      this.assertSecureTransport();
      await api.post("/auth/register", { 
        email, 
        password,
        user_name: user_name || null
      });
      // 注册成功后直接使用同一明文密码登录
      await this.login(email, password);
    },
    async fetchProfile() {
      if (!this.token) return;
      const { data } = await api.get("/auth/me");
      this.profile = data;
    },
    async changePassword(oldPassword: string, newPassword: string) {
      this.assertSecureTransport();
      await api.post("/auth/change-password", {
        old_password: oldPassword,
        new_password: newPassword
      });
    },
    logout() {
      this.clearClientCache();
      this.token = "";
      this.profile = null;
      localStorage.removeItem("token");
      writeCapacitorPrefs("token", "");
    }
  }
});

