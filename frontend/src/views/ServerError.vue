<template>
  <div class="min-h-screen bg-primary text-gray-900 flex items-center justify-center px-4">
    <div class="w-full max-w-md bg-white rounded-3xl shadow-float p-8 text-center">
      <div class="text-5xl font-extrabold tracking-tight text-gray-900">500</div>
      <div class="mt-3 text-lg font-semibold">服务暂时不可用</div>
      <div class="mt-2 text-sm text-gray-500">可能是网络波动或服务端异常，请稍后重试。</div>

      <div class="mt-8 flex items-center justify-center gap-3">
        <button class="btn ghost" @click="reload">刷新页面</button>
        <button class="btn primary" @click="goHome">回到首页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

/**
 * 刷新页面，用于重试加载。
 */
const reload = () => {
  window.location.reload();
};

/**
 * 回到首页。
 */
const goHome = () => {
  router.replace({ name: "home" });
};
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>
