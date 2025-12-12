<template>
  <Teleport to="body">
    <div class="fixed bottom-6 right-6 flex flex-col items-end gap-3">
    <!-- 刷新按钮（始终显示，位置会根据菜单是否打开而改变） -->
    <button class="fab-main" @click="handleRefresh" title="刷新页面">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
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
    <button class="fab-main" @click="open = !open">
      <span v-if="open">×</span>
      <span v-else>＋</span>
    </button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from "vue";

defineEmits<{
  home: [];
  notes: [];
  ledgers: [];
  statistics: [];
  settings: [];
}>();

const open = ref(false);

const handleRefresh = () => {
  location.reload();
};
</script>

<style scoped>
.fab-main {
  @apply w-14 h-14 rounded-full bg-gray-900 text-white text-2xl shadow-float flex items-center justify-center transition-transform duration-200 active:scale-95;
}
.fab-sub {
  @apply px-3 py-2 rounded-full bg-white shadow-float text-sm text-gray-700 hover:-translate-y-1 transition-all duration-200;
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
</style>

