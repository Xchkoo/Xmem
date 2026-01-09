import { defineStore } from "pinia";
import api from "../api/client";
import { hashPassword } from "../utils/crypto";
import { useDataStore } from "./data";

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
        // 前端加密密码
        const hashedPassword = await hashPassword(password);
        const { data } = await api.post("/auth/login", { email, password: hashedPassword });
        this.token = data.access_token;
        localStorage.setItem("token", data.access_token);
        await this.fetchProfile();
      } finally {
        this.loading = false;
      }
    },
    async register(email: string, password: string, user_name?: string) {
      // 前端加密密码
      const hashedPassword = await hashPassword(password);
      await api.post("/auth/register", { 
        email, 
        password: hashedPassword,
        user_name: user_name || null
      });
      // 注册成功后直接使用加密后的密码登录
      await this.login(email, password);
    },
    async fetchProfile() {
      if (!this.token) return;
      const { data } = await api.get("/auth/me");
      this.profile = data;
    },
    async changePassword(oldPassword: string, newPassword: string) {
      // 前端加密密码
      const hashedOldPassword = await hashPassword(oldPassword);
      const hashedNewPassword = await hashPassword(newPassword);
      await api.post("/auth/change-password", {
        old_password: hashedOldPassword,
        new_password: hashedNewPassword
      });
    },
    logout() {
      this.clearClientCache();
      this.token = "";
      this.profile = null;
      localStorage.removeItem("token");
    }
  }
});

