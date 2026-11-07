import { onUnmounted, ref, watch, type Ref } from "vue";
import api from "../api/client";

/**
 * 带鉴权的图片加载。
 *
 * 记账原图放在受保护接口 /ledger/images/{name} 后面（需要 Bearer token），
 * 不能直接写进 <img src>，这里用 axios 取 blob 再转成 object URL。
 */
export function useAuthedImage(source: Ref<string | null | undefined>) {
  const objectUrl = ref("");
  let current: string | null = null;

  const revoke = () => {
    if (current) {
      URL.revokeObjectURL(current);
      current = null;
    }
    objectUrl.value = "";
  };

  watch(
    source,
    async (path) => {
      revoke();
      if (!path) return;
      try {
        const response = await api.get(path, { responseType: "blob" });
        current = URL.createObjectURL(response.data as Blob);
        objectUrl.value = current;
      } catch {
        // 加载失败时保持空，由调用方回落到占位
        objectUrl.value = "";
      }
    },
    { immediate: true },
  );

  onUnmounted(revoke);

  return objectUrl;
}
