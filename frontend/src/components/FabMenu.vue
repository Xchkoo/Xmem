<template>
  <Teleport to="body">
    <div v-if="open && isMobile" class="fab-overlay" @click="closeMenu"></div>
    <div class="fab-wrapper" :class="{ 'fab-collapsed': shouldCollapse }" data-onboarding="fab-menu">
    <!-- 刷新按钮（始终显示，位置会根据菜单是否打开而改变） -->
    <button v-if="!isMobile || open" class="fab-main" @click="handleRefresh" title="刷新页面">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>
    <!-- AI 助手入口（与刷新、主题同层级，低调但可识别） -->
    <button
      v-if="!isMobile || open"
      class="fab-main ai-main"
      title="Xia 助手"
      aria-label="Xia 助手"
      @click="$emit('assistant')"
    >
      <svg class="ai-icon" width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
        <defs>
          <linearGradient id="aiGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="var(--xia-c1)" />
            <stop offset="100%" stop-color="var(--xia-c2)" />
          </linearGradient>
        </defs>
        <g fill="none" stroke="url(#aiGrad)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6.5" y="6.5" width="11" height="11" rx="2.2" />
          <path d="M4 9v-2M4 17v-2M20 9v-2M20 17v-2M9 4h2M13 4h2M9 20h2M13 20h2" />
        </g>
        <path
          d="M12 8.4l1.1 2.1 2.4.3-1.8 1.5.5 2.3-2.2-1.2-2.2 1.2.5-2.3-1.8-1.5 2.4-.3z"
          fill="url(#aiGrad)"
        />
      </svg>
    </button>
    <!-- 主题切换按钮（始终显示，位置会根据菜单是否打开而改变） -->
    <button
      v-if="!isMobile || open"
      class="fab-main"
      :class="{ 'opacity-60 cursor-not-allowed': isThemeToggleLocked }"
      :title="themeButtonTitle"
      :aria-disabled="isThemeToggleLocked"
      @click="handleThemeToggle"
    >
      <svg
        v-if="displayedTheme === 'light'"
        xmlns="http://www.w3.org/2000/svg"
        class="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"
        />
      </svg>
      <svg
        v-else-if="displayedTheme === 'dark'"
        xmlns="http://www.w3.org/2000/svg"
        class="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 3v2m0 14v2m9-9h-2M5 12H3m15.364-6.364l-1.414 1.414M7.05 16.95l-1.414 1.414m0-11.314l1.414 1.414m11.314 11.314l1.414 1.414M12 8a4 4 0 100 8 4 4 0 000-8z"
        />
      </svg>
    </button>
    <!-- 菜单项（当打开时显示在刷新按钮和主菜单按钮之间） -->
    <transition-group name="fade">
      <!-- 从上到下：主界面、笔记库、记账库、统计、设置 -->
      <button
        v-if="open"
        key="home"
        class="fab-sub"
        @click="$emit('home')"
      >
        🏠 主界面
      </button>
      <button
        v-if="open"
        key="notes"
        class="fab-sub"
        @click="$emit('notes')"
      >
        📒 笔记库
      </button>
      <button
        v-if="open"
        key="ledgers"
        class="fab-sub"
        @click="$emit('ledgers')"
      >
        📝 记账库
      </button>
      <button
        v-if="open"
        key="todos"
        class="fab-sub"
        @click="$emit('todos')"
      >
        ✅ 待办事项
      </button>
      <button
        v-if="open"
        key="statistics"
        class="fab-sub"
        @click="$emit('statistics')"
      >
        📊 统计
      </button>
      <button
        v-if="open"
        key="settings"
        class="fab-sub"
        @click="$emit('settings')"
      >
        ⚙ 设置
      </button>
    </transition-group>
    <!-- 主菜单按钮 -->
    <button class="fab-main" @click="toggleMenu">
      <span v-if="open">×</span>
      <span v-else>＋</span>
    </button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useThemeStore } from "../stores/theme";

defineEmits<{
  home: [];
  assistant: [];
  notes: [];
  ledgers: [];
  todos: [];
  statistics: [];
  settings: [];
}>();

const open = ref(false);
const isMobile = ref(false);
const theme = useThemeStore();

const displayedTheme = computed(() => (theme.selectedMode === "auto" ? theme.resolvedTheme : theme.selectedMode));
const isThemeToggleLocked = computed(() => theme.selectedMode === "auto");
const shouldCollapse = computed(() => isMobile.value && !open.value);

const themeButtonTitle = computed(() => {
  if (isThemeToggleLocked.value) return "已启用跟随系统，主题切换已锁定";
  if (displayedTheme.value === "light") return "切换主题：白天 → 黑夜";
  return "切换主题：黑夜 → 白天";
});

/**
 * 在非跟随系统时切换白天/黑夜主题。
 */
const handleThemeToggle = () => {
  if (isThemeToggleLocked.value) return;
  theme.setMode(displayedTheme.value === "dark" ? "light" : "dark");
};

/** 刷新页面 */
const handleRefresh = () => {
  location.reload();
};

/** 更新移动端判定 */
const updateIsMobile = () => {
  isMobile.value = window.matchMedia("(max-width: 640px)").matches;
};

/** 切换主菜单展开状态 */
const toggleMenu = () => {
  open.value = !open.value;
};

/** 关闭主菜单 */
const closeMenu = () => {
  open.value = false;
};

onMounted(() => {
  updateIsMobile();
  window.addEventListener("resize", updateIsMobile);
});

onUnmounted(() => {
  window.removeEventListener("resize", updateIsMobile);
});
</script>

<style scoped>
.fab-wrapper {
  @apply fixed bottom-6 right-6 flex flex-col items-end gap-3 transition-transform duration-200 z-50;
  /* 让出底部手势条/导航栏的安全区，避免按钮被系统栏盖住 */
  bottom: calc(1.5rem + var(--sab, 0px));
}
.fab-overlay {
  @apply fixed inset-0 z-40;
}
.fab-main {
  @apply w-14 h-14 rounded-full text-2xl flex items-center justify-center transition-transform duration-200 active:scale-95 hover:ring-4 hover:ring-accent/20;
}
.fab-sub {
  @apply px-3 py-2 rounded-full text-sm transition-all duration-200;
}
:is(.fab-main, .fab-sub) {
  background-color: var(--fab-bg);
  color: var(--fab-text);
  border: 1px solid var(--fab-border);
  box-shadow: var(--fab-shadow);
}
.fab-sub:hover {
  transform: translateY(-4px);
}
.ai-main {
  font-weight: 700;
  letter-spacing: 0.2px;
  --xia-c1: #5b9dff;
  --xia-c2: #ff82c8;
}
.ai-icon {
  display: block;
  filter: drop-shadow(0 6px 10px rgba(91, 157, 255, 0.25));
}
.ai-main:hover {
  border-color: var(--fab-border-hover);
  box-shadow: var(--fab-shadow-hover);
  @apply ring-4 ring-accent/20;
}
:global(.dark) .ai-main {
  --xia-c1: #9fc2ff;
  --xia-c2: #ffaddb;
  border-color: rgba(160, 200, 255, 0.30);
  box-shadow: 0 8px 18px rgba(160, 200, 255, 0.12);
}
:global(html[data-theme="light"]) .fab-wrapper {
  --fab-bg: rgb(255, 255, 255);
  --fab-text: rgb(31, 41, 55);
  --fab-border: rgba(90, 170, 255, 0.18);
  --fab-border-hover: rgba(90, 170, 255, 0.32);
  --fab-shadow: 0 6px 14px rgba(90, 170, 255, 0.10);
  --fab-shadow-hover: 0 10px 20px rgba(90, 170, 255, 0.14);
}
:global(html[data-theme="dark"]) .fab-wrapper {
  --fab-bg: rgb(17, 24, 39);
  --fab-text: rgb(255, 255, 255);
  --fab-border: rgba(160, 200, 255, 0.30);
  --fab-border-hover: rgba(160, 200, 255, 0.42);
  --fab-shadow: 0 8px 18px rgba(160, 200, 255, 0.12);
  --fab-shadow-hover: 0 10px 22px rgba(160, 200, 255, 0.16);
}
.fab-collapsed {
  right: -28px;
  bottom: calc(16px + var(--sab, 0px));
  transform: none;
}
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
@media (min-width: 641px) {
  .fab-collapsed {
    right: 1.5rem;
    bottom: calc(1.5rem + var(--sab, 0px));
  }
}
</style>
