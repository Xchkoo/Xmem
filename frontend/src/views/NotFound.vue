<template>
  <div class="min-h-screen bg-primary text-gray-900 flex items-center justify-center px-4">
    <div class="w-full max-w-md bg-white rounded-3xl shadow-float p-8 text-center">
      <div class="text-5xl font-extrabold tracking-tight text-gray-900">404</div>
      <div class="mt-3 text-lg font-semibold">页面不存在</div>
      <div class="mt-2 text-sm text-gray-500">你访问的地址可能已被移动或删除。</div>

      <div class="mt-8 flex items-center justify-center gap-3">
        <button class="btn ghost" @click="goBack">返回上一页</button>
        <button class="btn primary" @click="goHome">回到首页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

/**
 * 返回上一页；如果历史栈不足则回到首页。
 */
const goBack = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.replace({ name: "home" });
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
