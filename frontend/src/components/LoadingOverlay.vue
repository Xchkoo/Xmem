<template>
  <transition
    enter-active-class="transition-opacity duration-150"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="shouldShow"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-white/55 backdrop-blur-sm"
      role="status"
      aria-live="polite"
      aria-label="加载中"
    >
      <div class="flex flex-col items-center gap-4">
        <div class="relative h-12 w-12">
          <div class="absolute inset-0 rounded-full border-4 border-gray-200" />
          <div class="absolute inset-0 rounded-full border-4 border-accent border-t-transparent animate-spin" />
        </div>

        <div class="flex items-center gap-2 text-sm font-medium text-gray-600">
          <span class="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.2s]" />
          <span class="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.1s]" />
          <span class="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce" />
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    visible: boolean;
    delayMs?: number;
  }>(),
  {
    delayMs: 150,
  }
);

const shouldShow = ref(false);
let showTimer: number | null = null;

const clearTimer = () => {
  if (showTimer === null) return;
  window.clearTimeout(showTimer);
  showTimer = null;
};

watch(
  () => props.visible,
  (next) => {
    clearTimer();
    if (!next) {
      shouldShow.value = false;
      return;
    }

    showTimer = window.setTimeout(() => {
      shouldShow.value = true;
      showTimer = null;
    }, props.delayMs);
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  clearTimer();
});
</script>

