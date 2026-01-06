import { replaceImagesWithSecureUrls } from "../utils/secureImages";
import { handleSecureDownload, isSecureResource } from "../utils/secureDownload";

// 防抖函数，避免在打字时频繁触发图片替换
function debounce(fn: Function, delay: number) {
  let timeoutId: any;
  return function (...args: any[]) {
    if (timeoutId) clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      fn.apply(null, args);
    }, delay);
  };
}

export const vSecureDisplay = {
  mounted(el: HTMLElement) {
    // 1. 事件代理：直接在容器上监听点击事件，拦截文件下载
    // 这样不需要为每个链接单独绑定，性能更好且支持动态添加的内容
    const clickHandler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a');
      
      // 检查是否是受保护的文件链接
      if (link && link.href && isSecureResource(link.href)) {
        e.preventDefault();
        e.stopPropagation();
        handleSecureDownload(link.href);
      }
    };
    
    el.addEventListener('click', clickHandler);
    (el as any).__secureClickHandler = clickHandler;

    // 2. 图片鉴权替换逻辑
    // 使用防抖，避免编辑器频繁更新导致频繁请求
    const handleImages = debounce(() => {
      // 限制在当前元素内查找，支持多实例，性能更好
      // 尝试查找预览区域 wrapper (MdEditor) 或直接是当前元素 (MdPreview)
      const previewArea = el.querySelector('.md-editor-preview-wrapper') || el;
      replaceImagesWithSecureUrls(previewArea as HTMLElement);
    }, 300);

    // 立即执行一次
    handleImages();

    // 3. 监听 DOM 变化
    const observer = new MutationObserver((mutations) => {
      let shouldUpdate = false;
      for (const mutation of mutations) {
        // 只有当节点增加或 src 属性变化时才更新
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          shouldUpdate = true;
          break;
        }
        if (mutation.type === 'attributes' && (mutation.attributeName === 'src' || mutation.attributeName === 'href')) {
          shouldUpdate = true;
          break;
        }
      }
      
      if (shouldUpdate) {
        handleImages();
      }
    });

    observer.observe(el, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['src', 'href'] // 只关心 src 和 href 变化
    });

    (el as any).__secureObserver = observer;
  },

  unmounted(el: HTMLElement) {
    // 清理事件监听
    if ((el as any).__secureClickHandler) {
      el.removeEventListener('click', (el as any).__secureClickHandler);
      delete (el as any).__secureClickHandler;
    }

    // 清理观察者
    if ((el as any).__secureObserver) {
      (el as any).__secureObserver.disconnect();
      delete (el as any).__secureObserver;
    }
  }
};
