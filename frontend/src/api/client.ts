import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 8000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理错误，但不自动清除 token（让组件决定）
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 如果是 401 未授权，可能是 token 过期，但不自动清除
    // 让组件根据具体情况决定是否清除 token
    if (error.response?.status === 401) {
      console.warn("API 请求未授权，可能需要重新登录");
    }
    return Promise.reject(error);
  }
);

export default api;

