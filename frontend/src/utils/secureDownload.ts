import api from "../api/client";
import { useToastStore } from "../stores/toast";

/**
 * 处理受保护文件的下载
 * @param url 文件 URL
 * @param fileName 文件名（可选）
 */
export const handleSecureDownload = async (url: string, fileName?: string) => {
  const toast = useToastStore();
  
  try {
    toast.info("正在准备下载...");
    
    // 处理 URL
    // api.get 使用 baseURL (通常是 /api)，所以我们需要根据 baseURL 调整请求路径
    let requestPath = url;
    const baseURL = api.defaults.baseURL || "/api";
    // 移除可能存在的末尾斜杠
    const cleanApiUrl = baseURL.endsWith("/") ? baseURL.slice(0, -1) : baseURL;
    
    // 如果 URL 以 cleanApiUrl 开头 (例如 /api/notes/files/...)，去除它
    if (url.startsWith(cleanApiUrl)) {
      requestPath = url.substring(cleanApiUrl.length);
    } 
    // 或者如果 URL 只是以 /notes/files/... 开头，且 baseURL 也是 /api，通常 api client 会自动拼接
    // 但如果 url 已经是完整的 http://... 则需要特殊处理，不过这里假设主要是相对路径或同源绝对路径
    
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
