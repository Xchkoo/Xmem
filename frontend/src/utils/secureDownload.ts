import api from "../api/client";
import { useToastStore } from "../stores/toast";

/**
 * 检查 URL 是否是内部受保护资源
 */
export const isSecureResource = (url: string): boolean => {
  if (!url) return false;
  
  const baseURL = api.defaults.baseURL || "/api";
  
  // 1. 相对路径
  if (url.startsWith("/")) {
    return url.includes("/notes/files/");
  }
  
  // 2. 绝对路径
  if (url.startsWith("http")) {
    if (baseURL.startsWith("http")) {
      // 必须匹配配置的 API Base URL
      return url.startsWith(baseURL) && url.includes("/notes/files/");
    } else {
      // 如果 baseURL 是相对路径 (e.g. /api)，检查是否匹配当前 origin + baseURL
      const currentOrigin = window.location.origin;
      if (url.startsWith(currentOrigin)) {
        const path = url.substring(currentOrigin.length);
        return path.startsWith(baseURL) && path.includes("/notes/files/");
      }
    }
  }
  
  return false;
};

/**
 * 处理受保护文件的下载
 * @param url 文件 URL
 * @param fileName 文件名（可选）
 */
export const handleSecureDownload = async (url: string, fileName?: string) => {
  const toast = useToastStore();
  
  // 双重检查：确保只处理内部资源
  if (!isSecureResource(url)) {
    // 如果不是内部资源，直接打开新窗口（如果是下载链接，浏览器会自动处理）
    window.open(url, '_blank');
    return;
  }
  
  try {
    toast.info("正在准备下载...");
    
    // 处理 URL
    // api.get 使用 baseURL (通常是 /api)，所以我们需要根据 baseURL 调整请求路径
    let requestPath = url;
    const baseURL = api.defaults.baseURL || "/api";
    // 移除可能存在的末尾斜杠
    const cleanApiUrl = baseURL.endsWith("/") ? baseURL.slice(0, -1) : baseURL;
    
    // 如果 URL 以 cleanApiUrl 开头 (例如 /api/notes/files/...)，去除它
    if (url.startsWith("http")) {
        if (baseURL.startsWith("http") && url.startsWith(baseURL)) {
             requestPath = url.substring(baseURL.length);
        } else {
             const currentOrigin = window.location.origin;
             if (url.startsWith(currentOrigin)) {
                 const path = url.substring(currentOrigin.length);
                 if (path.startsWith(cleanApiUrl)) {
                     requestPath = path.substring(cleanApiUrl.length);
                 }
             }
        }
    } else if (url.startsWith(cleanApiUrl)) {
      requestPath = url.substring(cleanApiUrl.length);
    } 
    
    // 发起带 Token 的请求
    const response = await api.get(requestPath, {
      responseType: "blob",
    });

    // 创建 Blob URL
    const blobUrl = URL.createObjectURL(response.data);
    
    // 创建临时链接触发下载
    const link = document.createElement("a");
    link.href = blobUrl;
    
    // 确定文件名
    let downloadName = fileName;
    if (!downloadName) {
      // 尝试从 Content-Disposition 获取
      const contentDisposition = response.headers["content-disposition"];
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match && match[1]) {
          downloadName = match[1];
        }
      }
    }
    if (!downloadName) {
      downloadName = url.split("/").pop() || "download";
    }
    
    link.download = downloadName;
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    
    toast.success("下载已开始");
  } catch (error) {
    console.error("下载失败:", error);
    toast.error("下载失败，请重试");
  }
};
