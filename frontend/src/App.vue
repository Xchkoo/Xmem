  <template>
    <div class="min-h-screen bg-bg text-text" :class="{ 'ai-docked': isAssistantDocked }">
      <router-view />

      <transition
        enter-active-class="transition-opacity duration-150"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="ui.routeBar"
          class="fixed top-0 left-0 right-0 z-[55] h-[3px] bg-accent/80 animate-pulse"
        />
      </transition>

      <LoadingOverlay :visible="ui.routeLoading" />

      <FabMenu
        v-if="user.token && !route.path.includes('/editor')"
        @settings="showSettings = true"
        @assistant="showAssistant = true"
        @notes="router.push('/notes')"
        @home="router.push('/')"
        @ledgers="router.push('/ledgers')"
        @todos="router.push('/todos')"
        @statistics="router.push('/statistics')"
      />

      <Settings v-if="user.token" :visible="showSettings" @close="showSettings = false" />
      <AiAssistant
        v-if="user.token && !route.path.includes('/editor')"
        :visible="showAssistant"
        :isDesktop="isDesktop"
        :docked="isAssistantDocked"
        @close="showAssistant = false"
      />

      <Toast />

      <ConfirmDialog
        :visible="confirm.visible"
        :title="confirm.title"
        :message="confirm.message"
        :confirm-text="confirm.confirmText"
        :cancel-text="confirm.cancelText"
        :type="confirm.type"
        @confirm="confirm.confirm()"
        @cancel="confirm.cancel()"
      />

      <LedgerEditor
        :visible="ledgerEditor.visible"
        :ledger="ledgerEditor.ledger"
        @close="ledgerEditor.close()"
        @saved="ledgerEditor.close()"
      />
    </div>
  </template>

  <script setup lang="ts">
  import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
  import { useRouter, useRoute } from "vue-router";
  import { driver, type Driver } from "driver.js";
  import FabMenu from "./components/FabMenu.vue";
  import Settings from "./components/Settings.vue";
  import Toast from "./components/Toast.vue";
  import ConfirmDialog from "./components/ConfirmDialog.vue";
  import LedgerEditor from "./components/LedgerEditor.vue";
  import LoadingOverlay from "./components/LoadingOverlay.vue";
  import AiAssistant from "./components/AiAssistant.vue";
  import { useUserStore } from "./stores/user";
  import { useConfirmStore } from "./stores/confirm";
  import { usePreferencesStore } from "./stores/preferences";
  import { useLedgerEditorStore } from "./stores/ledgerEditor";
  import { useUiStore } from "./stores/ui";
  import { nativeCapture } from "./utils/nativeCapture";

  const router = useRouter();
  const route = useRoute();
  const user = useUserStore();
  const confirm = useConfirmStore();
  const ledgerEditor = useLedgerEditorStore();
  const ui = useUiStore();
  usePreferencesStore().init();

  // 全局 UI 状态
  const showSettings = ref(false);
  const showAssistant = ref(false);
  const windowWidth = ref(typeof window !== "undefined" ? window.innerWidth : 1200);
  const isDesktop = computed(() => windowWidth.value > 900);
  const isAssistantDocked = computed(() => isDesktop.value && showAssistant.value);
  const onboardingDriver = ref<Driver | null>(null);
  const onboardingActive = ref(false);
  const onboardingKey = "xmem_onboarding_done";
  const onboardingPopoverClass = "xmem-onboarding-popover";

  /**
   * 同步窗口宽度到本地状态。
   */
  const syncWindowWidth = () => {
    windowWidth.value = window.innerWidth;
  };

  /**
   * 判断是否已完成新手引导。
   */
  const isOnboardingDone = () => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem(onboardingKey) === "1";
  };

  /**
   * 标记新手引导已完成，并释放状态。
   */
  const markOnboardingDone = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem(onboardingKey, "1");
    }
    onboardingActive.value = false;
  };

  const getTabFromQuery = () => {
    const raw = Array.isArray(route.query.tab) ? route.query.tab[0] : route.query.tab;
    return raw === "note" || raw === "ledger" ? raw : "note";
  };

  const waitForTab = (expected: "note" | "ledger", timeoutMs: number = 4000) => {
    return new Promise<boolean>((resolve) => {
      if (typeof window === "undefined") {
        resolve(false);
        return;
      }
      if (getTabFromQuery() === expected) {
        resolve(true);
        return;
      }
      const startedAt = Date.now();
      const timer = window.setInterval(() => {
        if (getTabFromQuery() === expected) {
          window.clearInterval(timer);
          resolve(true);
          return;
        }
        if (Date.now() - startedAt >= timeoutMs) {
          window.clearInterval(timer);
          resolve(false);
        }
      }, 80);
    });
  };

/**
 * 等待首页 Tab 状态同步到全局信号。
 */
const waitForHomeTab = (expected: "note" | "ledger", timeoutMs: number = 4000) => {
  return new Promise<boolean>((resolve) => {
    if (typeof window === "undefined") {
      resolve(false);
      return;
    }
    const readSignal = () => (window as any).__xmemHomeTab as "note" | "ledger" | undefined;
    if (readSignal() === expected) {
      resolve(true);
      return;
    }
    const startedAt = Date.now();
    const timer = window.setInterval(() => {
      if (readSignal() === expected) {
        window.clearInterval(timer);
        resolve(true);
        return;
      }
      if (Date.now() - startedAt >= timeoutMs) {
        window.clearInterval(timer);
        resolve(false);
      }
    }, 80);
  });
};

  /**
   * 等待引导目标元素出现在 DOM 中。
   */
  const waitForElement = (selector: string, timeoutMs: number = 8000) => {
    return new Promise<HTMLElement | null>((resolve) => {
      if (typeof window === "undefined") {
        resolve(null);
        return;
      }
      const existing = document.querySelector(selector) as HTMLElement | null;
      if (existing) {
        resolve(existing);
        return;
      }
      const startedAt = Date.now();
      const timer = window.setInterval(() => {
        const found = document.querySelector(selector) as HTMLElement | null;
        if (found) {
          window.clearInterval(timer);
          resolve(found);
          return;
        }
        if (Date.now() - startedAt >= timeoutMs) {
          window.clearInterval(timer);
          resolve(null);
        }
      }, 120);
    });
  };

  /**
   * 导航并等待引导目标元素就绪。
   */
  const navigateAndWait = async (
    path: string,
    query: Record<string, string> | undefined,
    selector: string,
    expectedTab?: "note" | "ledger"
  ) => {
    try {
      await router.push({ path, query });
    } catch {
      // 忽略重复导航
    }
    await nextTick();
    if (expectedTab) {
      await waitForTab(expectedTab);
    }
    return waitForElement(selector);
  };

  /**
   * 进入指定步骤并在元素出现后移动到下一步或上一步。
   */
  const goToStep = async (
    path: string,
    query: Record<string, string> | undefined,
    selector: string,
    direction: "next" | "prev",
    expectedTab?: "note" | "ledger"
  ) => {
    const target = await navigateAndWait(path, query, selector, expectedTab);
    if (!target) {
      onboardingDriver.value?.destroy();
      markOnboardingDone();
      return;
    }
    if (direction === "next") {
      onboardingDriver.value?.moveNext();
    } else {
      onboardingDriver.value?.movePrevious();
    }
  };

  /**
   * 切换首页 Tab 并等待目标元素出现后推进引导步骤。
   */
  const goToHomeTabStep = async (
    tab: "note" | "ledger",
    selector: string,
    direction: "next" | "prev"
  ) => {
    try {
      await router.replace({ path: "/", query: { ...route.query, tab } });
    } catch {
      // 忽略重复导航
    }
    await nextTick();
    await waitForTab(tab);
    const homeReady = await waitForHomeTab(tab);
    if (!homeReady || getTabFromQuery() !== tab) {
      const button = await waitForElement(`[data-onboarding="tab-${tab}"]`, 4000);
      if (button) {
        button.click();
        await nextTick();
        await waitForTab(tab);
        await waitForHomeTab(tab);
      }
    }
    onboardingDriver.value?.refresh();
    const target = await waitForElement(selector);
    if (!target) {
      onboardingDriver.value?.destroy();
      markOnboardingDone();
      return;
    }
    if (direction === "next") {
      onboardingDriver.value?.moveNext();
    } else {
      onboardingDriver.value?.movePrevious();
    }
  };

  /**
   * 启动新用户引导流程。
   */
  const startOnboarding = async () => {
    if (onboardingActive.value || isOnboardingDone()) return;
    onboardingActive.value = true;
    await navigateAndWait("/", { tab: "note" }, '[data-onboarding="quick-input"]', "note");

    const driverInstance = driver({
      nextBtnText: "下一步",
      prevBtnText: "上一步",
      doneBtnText: "完成",
      showProgress: true,
      popoverClass: onboardingPopoverClass,
      onPopoverRender: (popover) => {
        const closeButton = popover.closeButton;
        const footerButtons = popover.footerButtons;
        const previousButton = popover.previousButton;
        if (closeButton && footerButtons && previousButton) {
          closeButton.textContent = "跳过";
          if (!footerButtons.contains(closeButton)) {
            footerButtons.insertBefore(closeButton, previousButton);
          }
        }
      },
      onDestroyStarted: () => {
        markOnboardingDone();
        onboardingDriver.value?.destroy();
      },
      steps: [
        {
          element: "body",
          popover: {
            title: "欢迎使用 Xmem",
            description: "第一次使用 Xmem？这里有个简单的教程可以帮助你快速上手。",
            side: "over",
            align: "center",
            showProgress: false,
            showButtons: ["close", "next"],
            onNextClick: async () => {
              await goToStep("/", { tab: "note" }, '[data-onboarding="quick-input"]', "next", "note");
            },
          },
        },
        {
          element: '[data-onboarding="quick-input"]',
          popover: {
            title: "笔记快速输入",
            description: "在笔记模式可通过输入框快速创建笔记，也能打开编辑器使用 Markdown。",
            onPrevClick: () => {
              onboardingDriver.value?.movePrevious();
            },
            onNextClick: async () => {
              await goToStep("/notes", undefined, '[data-onboarding="notes-search"]', "next");
            },
          },
        },
        {
          element: '[data-onboarding="notes-search"]',
          popover: {
            title: "笔记库与导出",
            description: "这里可以搜索全部笔记。",
            onPrevClick: async () => {
              await goToStep("/", { tab: "note" }, '[data-onboarding="quick-input"]', "prev", "note");
            },
            onNextClick: async () => {
              await goToStep("/notes", undefined, '[data-onboarding="notes-export"]', "next");
            },
          },
        },
        {
          element: '[data-onboarding="notes-export"]',
          popover: {
            title: "导出笔记",
            description: "这里可以导出笔记",
            onPrevClick: async () => {
              await goToStep("/notes", undefined, '[data-onboarding="notes-search"]', "prev");
            },
            onNextClick: async () => {
              await goToStep("/", { tab: "note" }, '[data-onboarding="todo-panel"]', "next", "note");
            },
          },
        },
        {
          element: '[data-onboarding="todo-panel"]',
          popover: {
            title: "待办事项",
            description: "待办支持输入创建与回车创建待办组，查看全部可看到已完成事项。",
            onPrevClick: async () => {
              await goToStep("/notes", undefined, '[data-onboarding="notes-search"]', "prev");
            },
            onNextClick: async () => {
              await goToHomeTabStep("ledger", '[data-onboarding="ledger-quick-input-anchor"]', "next");
            },
          },
        },
        {
          element: () => document.querySelector('[data-onboarding="quick-input"]') as Element,
          popover: {
            title: "记账快速输入",
            description: "记账模式支持上传图片和文本描述，提交后可看到状态变化。",
            onPrevClick: async () => {
              await goToStep("/", { tab: "note" }, '[data-onboarding="todo-panel"]', "prev", "note");
            },
            onNextClick: async () => {
              await goToStep("/ledgers", undefined, '[data-onboarding="ledger-category-filter"]', "next");
            },
          },
        },
        {
          element: '[data-onboarding="ledger-category-filter"]',
          popover: {
            title: "记账库筛选",
            description: "记账库可查看全部记录，并通过分类筛选快速定位。",
            onPrevClick: async () => {
              await goToStep("/", { tab: "ledger" }, '[data-onboarding="quick-input"]', "prev", "ledger");
            },
            onNextClick: async () => {
              await goToStep("/statistics", undefined, '[data-onboarding="statistics-overview"]', "next");
            },
          },
        },
        {
          element: '[data-onboarding="statistics-overview"]',
          popover: {
            title: "支出统计",
            description: "统计界面包含 AI 总结、预算与多种图表，帮助理解支出结构。",
            onPrevClick: async () => {
              await goToStep("/ledgers", undefined, '[data-onboarding="ledger-category-filter"]', "prev");
            },
            onNextClick: async () => {
              await goToStep("/", { tab: "ledger" }, '[data-onboarding="ledger-note-generator"]', "next", "ledger");
            },
          },
        },
        {
          element: '[data-onboarding="ledger-note-generator"]',
          popover: {
            title: "生成记账笔记",
            description: "支持自定义生成当日、本周、本月的记账笔记。",
            onPrevClick: async () => {
              await goToStep("/statistics", undefined, '[data-onboarding="statistics-overview"]', "prev");
            },
            onNextClick: async () => {
              await goToStep("/", { tab: "note" }, '[data-onboarding="fab-menu"]', "next", "note");
            },
          },
        },
        {
          element: '[data-onboarding="fab-menu"]',
          popover: {
            title: "功能面板",
            description: "右下角可刷新、打开 AI 侧栏、切换主题与快捷路由。",
            onPrevClick: async () => {
              await goToStep("/", { tab: "ledger" }, '[data-onboarding="ledger-note-generator"]', "prev", "ledger");
            },
            onNextClick: () => {
              onboardingDriver.value?.moveNext();
            },
          },
        },
        {
          element: "body",
          popover: {
            title: "完成引导",
            description: "你已经完全了解 Xmem 了，开始使用吧！",
            onPrevClick: async () => {
              await goToStep("/", { tab: "note" }, '[data-onboarding="fab-menu"]', "prev", "note");
            },
          },
        },
      ],
    });

    onboardingDriver.value = driverInstance;
    driverInstance.drive();
  };

  /**
   * 检查并在合适时机触发引导。
   */
  const maybeStartOnboarding = async () => {
    if (!user.token) return;
    if (route.name !== "home") return;
    if (onboardingActive.value || isOnboardingDone()) return;
    const anchor = await waitForElement('[data-onboarding="quick-input"]', 1200);
    if (!anchor || route.name !== "home") return;
    await startOnboarding();
  };

  onMounted(() => {
    window.addEventListener("resize", syncWindowWidth);
    maybeStartOnboarding();
    void syncNativeCapture();
    document.addEventListener("visibilitychange", handleVisibilityChange);
  });

  onUnmounted(() => {
    window.removeEventListener("resize", syncWindowWidth);
    document.removeEventListener("visibilitychange", handleVisibilityChange);
  });

  /**
   * 截屏记账的通知被点开后系统会打开 App，这里取出「待跳转的记账 id」并导航到详情。
   */
  const handlePendingLedger = async () => {
    const ledgerId = await nativeCapture.consumePendingLedger();
    if (ledgerId > 0) {
      await router.push({ name: "ledger-view", params: { ledgerId: String(ledgerId) } });
    }
  };

  /**
   * App 启动时把 token 同步给原生（磁贴/分享入口依赖它），并检查是否有待跳转的记账。
   */
  const syncNativeCapture = async () => {
    await user.syncNativeSession();
    await handlePendingLedger();
  };

  const handleVisibilityChange = () => {
    if (document.visibilityState === "visible") {
      void handlePendingLedger();
    }
  };

  watch(() => route.path, (path) => {
    if (path.includes("/editor")) {
      showAssistant.value = false;
    }
  });

  watch([() => route.name, () => user.token], () => {
    maybeStartOnboarding();
  });

  </script>

  <style scoped>
  .ai-docked {
    padding-right: 460px;
  }
  :global(.xmem-onboarding-popover .driver-popover-close-btn) {
    position: static;
    width: auto;
    height: auto;
    margin-right: 6px;
    font-size: 12px;
    line-height: 1.3;
    color: #2d2d2d;
  }
  </style>
