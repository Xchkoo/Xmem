<template>
  <div class="fixed bottom-6 right-6 flex flex-col items-end gap-3">
    <transition-group name="fade">
      <button
        v-if="open"
        key="settings"
        class="fab-sub"
        @click="$emit('settings')"
      >
        ⚙ 设置
      </button>
      <button v-if="open" key="notes" class="fab-sub" @click="$emit('notes')">📒 笔记库</button>
      <button v-if="open" key="ledger" class="fab-sub" @click="$emit('ledger')">📊 记账汇总</button>
    </transition-group>
    <button class="fab-main" @click="open = !open">
      <span v-if="open">×</span>
      <span v-else>＋</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const open = ref(false);
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

