import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  timeout: 8000
});

let authRedirecting = false;

api.interceptors.request.use((config) => {
  /**
   * 判断当前请求是否属于认证相关的敏感请求。
   */
  const isAuthRequest = (url: unknown): boolean => {
    if (typeof url !== "string") return false;
    return url.startsWith("/auth/") || url.includes("/auth/");
  };

  /**
   * 校验认证请求是否在安全传输下发送。
   *
   * - 浏览器环境：页面本身必须是 https（本地开发除外）
   * - Electron 环境：页面可能是 file://，此时要求 API baseURL 必须是 https（本地开发除外）
   */
  const assertAuthRequestSecureTransport = () => {
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

    const apiBaseURL = (config.baseURL || api.defaults.baseURL || "").toString();
    const isApiHttps = apiBaseURL.startsWith("https://");

    if (protocol === "https:" || isLocalHost || isCapacitor) return;

    if (protocol === "file:" && isApiHttps) {
      return;
    }

    throw new Error("为保障账号安全，认证请求仅允许在 HTTPS 环境下发送");
  };

  if (isAuthRequest(config.url)) {
    assertAuthRequestSecureTransport();
  }

  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理错误，但不自动清除 token（让组件决定）
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    /**
     * 获取应用注入到 window 的 router 实例（用于避免 api -> router 的循环依赖）。
     */
    const getAppRouter = (): any => {
      if (typeof window === "undefined") return null;
      return (window as any).__xmemRouter || null;
    };

    const status = error?.response?.status;
    if (status === 401 || status === 403) {
      localStorage.removeItem("token");
      if (!authRedirecting) {
        authRedirecting = true;
        try {
          const router = getAppRouter();
          if (!router) throw new Error("router not ready");
          const current = router.currentRoute.value;
          const isAuthRoute = current.name === "login" || current.name === "register";
          if (!isAuthRoute) {
            await router.replace({ name: "login", query: { redirect: current.fullPath } });
          }
        } catch {
          const redirect = encodeURIComponent(window.location.pathname + window.location.search + window.location.hash);
          window.location.href = `/login?redirect=${redirect}`;
        } finally {
          authRedirecting = false;
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
