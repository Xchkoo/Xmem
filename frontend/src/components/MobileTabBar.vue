<template>
  <nav class="mobile-tabbar" role="navigation" aria-label="主导航">
    <!-- 左半边两个 tab -->
    <div class="side">
      <button
        v-for="tab in leftTabs"
        :key="tab.name"
        class="tab-item"
        :class="{ active: isActive(tab) }"
        type="button"
        @click="go(tab)"
      >
        <span class="tab-icon" v-html="tab.icon" />
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <!-- 中间凸起的「输入」：不是路由，是动作 -->
    <div class="tab-center">
      <button class="center-btn" type="button" aria-label="快速输入" @click="$emit('input')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
          <path stroke-linecap="round" d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </div>

    <!-- 右半边一个 tab，居中占满右半区 -->
    <div class="side side-right">
      <button
        v-for="tab in rightTabs"
        :key="tab.name"
        class="tab-item"
        :class="{ active: isActive(tab) }"
        type="button"
        @click="go(tab)"
      >
        <span class="tab-icon" v-html="tab.icon" />
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

interface TabItem {
  name: string;
  label: string;
  path: string;
  icon: string;
  match?: string[];
}

/**
 * 中间凸起（输入）不是路由，是动作。
 * 左边两个 tab、右边一个 tab，凸起正好落在栏的正中。
 * 待办/统计不进底栏，入口保持在记账页内。
 */
const TABS: TabItem[] = [
  {
    name: "notes",
    label: "笔记",
    path: "/notes",
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 4h7l4 4v12H7z"/><path stroke-linecap="round" d="M9 12h6M9 16h4"/></svg>',
    match: ["notes", "notebook", "note-view", "note-export"],
  },
  {
    name: "ledgers",
    label: "记账",
    path: "/ledgers",
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 7h16v13H4z"/><path stroke-linecap="round" d="M4 7l2-3h12l2 3"/><path stroke-linecap="round" d="M9 13h6"/></svg>',
    match: ["ledgers", "ledger-view", "statistics"],
  },
];

const leftTabs = computed(() => TABS.slice(0, 1));
const rightTabs = computed(() => TABS.slice(1));

const route = useRoute();
const router = useRouter();

defineEmits<{ (e: "input"): void }>();

const isActive = (tab: TabItem) => {
  const name = String(route.name ?? "");
  if (tab.match?.includes(name)) return true;
  return route.path === tab.path;
};

const go = (tab: TabItem) => {
  if (route.path === tab.path) return;
  router.push(tab.path);
};
</script>

<style scoped>
.mobile-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 90;
  display: grid;
  /* 左右两个等宽区 + 中间固定宽度留给凸起按钮 => 按钮严格居中 */
  grid-template-columns: 1fr 88px 1fr;
  align-items: center;
  height: 58px;
  padding-bottom: var(--sab, 0px);
  background: rgb(var(--c-surface) / 0.96);
  backdrop-filter: blur(12px);
  border-top: 1px solid rgb(var(--c-border));
  box-sizing: content-box;
}

.side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 100%;
}

/* 右侧只有一个设置，居中放在右半区 */
.side-right {
  grid-template-columns: 1fr;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  height: 100%;
  border: none;
  background: transparent;
  color: rgb(var(--c-text-muted));
  font-size: 11px;
  transition: color var(--theme-transition-ms) ease;
}

.tab-item.active {
  color: rgb(var(--c-text));
}

.tab-icon {
  display: flex;
  width: 22px;
  height: 22px;
}

.tab-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.tab-label {
  line-height: 1;
}

/* 中间的蓝色凸起按钮 */
.tab-center {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.center-btn {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  width: 62px;
  height: 62px;
  border: none;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(160deg, #4c8dff, #2f6bff);
  box-shadow: 0 8px 20px rgba(47, 107, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease;
}

.center-btn:active {
  transform: translateX(-50%) scale(0.94);
}

.center-btn svg {
  width: 26px;
  height: 26px;
}

/* 半圆底座：让按钮看起来是从底栏里"长"出来的 */
.center-btn::before {
  content: "";
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: rgb(var(--c-surface));
  z-index: -1;
}
</style>
