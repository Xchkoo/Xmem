<template>
  <Teleport to="body">
    <div class="toast-container fixed top-4 left-1/2 -translate-x-1/2 z-[9999] flex flex-col gap-4 pointer-events-none">
      <TransitionGroup name="toast" tag="div">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
            'toast-item pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg min-w-[300px] max-w-[500px] my-2',
            getToastClass(toast.type)
          ]"
        >
          <!-- 图标 -->
          <div :class="['flex-shrink-0', getIconClass(toast.type)]">
            <!-- Success Icon -->
            <svg
              v-if="toast.type === 'success'"
              xmlns="http://www.w3.org/2000/svg"
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <!-- Error Icon -->
            <svg
              v-else-if="toast.type === 'error'"
              xmlns="http://www.w3.org/2000/svg"
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <!-- Warning Icon -->
            <svg
              v-else-if="toast.type === 'warning'"
              xmlns="http://www.w3.org/2000/svg"
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <!-- Info Icon -->
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          <!-- 消息 -->
          <div class="flex-1 text-sm font-medium">{{ toast.message }}</div>

          <!-- 关闭按钮 -->
          <button
            @click="remove(toast.id)"
            class="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity p-1 rounded"
            :class="getCloseButtonClass(toast.type)"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useToastStore, type ToastType } from "../stores/toast";

const toastStore = useToastStore();

const toasts = computed(() => toastStore.toasts);

const remove = (id: string) => {
  toastStore.remove(id);
};

const getToastClass = (type: ToastType): string => {
  const classes = {
    success: "bg-green-500 text-white",
    error: "bg-red-500 text-white",
    warning: "bg-yellow-500 text-white",
    info: "bg-blue-500 text-white",
  };
  return classes[type] || classes.info;
};

const getIconClass = (type: ToastType): string => {
  const classes = {
    success: "text-green-100",
    error: "text-red-100",
    warning: "text-yellow-100",
    info: "text-blue-100",
  };
  return classes[type] || classes.info;
};

const getCloseButtonClass = (type: ToastType): string => {
  const classes = {
    success: "text-green-100 hover:bg-green-600",
    error: "text-red-100 hover:bg-red-600",
    warning: "text-yellow-100 hover:bg-yellow-600",
    info: "text-blue-100 hover:bg-blue-600",
  };
  return classes[type] || classes.info;
};
</script>

<style scoped>
/* Toast 动画 */
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.3s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-30px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-30px);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>

