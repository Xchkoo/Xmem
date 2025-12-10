<template>
  <Teleport to="body">
    <Transition name="confirm">
      <div
        v-if="visible"
        class="confirm-overlay fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
        @click.self="handleCancel"
      >
        <div class="confirm-dialog bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
          <!-- 标题 -->
          <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
          </div>

          <!-- 内容 -->
          <div class="px-6 py-4">
            <p class="text-gray-700">{{ message }}</p>
          </div>

          <!-- 按钮 -->
          <div class="px-6 py-4 bg-gray-50 flex justify-end gap-3">
            <button
              @click="handleCancel"
              class="px-4 py-2 rounded-lg font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              {{ cancelText }}
            </button>
            <button
              @click="handleConfirm"
              :class="[
                'px-4 py-2 rounded-lg font-medium text-white transition-colors',
                confirmButtonClass
              ]"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  visible: boolean;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: "danger" | "warning" | "info";
}

const props = withDefaults(defineProps<Props>(), {
  title: "确认",
  confirmText: "确认",
  cancelText: "取消",
  type: "danger",
});

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

const confirmButtonClass = computed(() => {
  const classes = {
    danger: "bg-red-500 hover:bg-red-600",
    warning: "bg-yellow-500 hover:bg-yellow-600",
    info: "bg-blue-500 hover:bg-blue-600",
  };
  return classes[props.type] || classes.danger;
});

const handleConfirm = () => {
  emit("confirm");
};

const handleCancel = () => {
  emit("cancel");
};
</script>

<style scoped>
/* 确认对话框动画 */
.confirm-enter-active,
.confirm-leave-active {
  transition: opacity 0.3s ease;
}

.confirm-enter-active .confirm-dialog,
.confirm-leave-active .confirm-dialog {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.confirm-enter-from,
.confirm-leave-to {
  opacity: 0;
}

.confirm-enter-from .confirm-dialog,
.confirm-leave-to .confirm-dialog {
  transform: scale(0.9) translateY(-20px);
  opacity: 0;
}
</style>


