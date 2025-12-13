<template>
  <div class="relative" ref="selectRef">
    <!-- 显示当前选中值的按钮 -->
    <button
      type="button"
      @click="toggleDropdown"
      :class="[
        'input w-full text-left flex items-center justify-between',
        isOpen ? 'border-gray-900' : ''
      ]"
    >
      <span :class="{ 'text-gray-400': !modelValue }">
        {{ displayText || placeholder }}
      </span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 text-gray-400 transition-transform"
        :class="{ 'rotate-180': isOpen }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- 下拉选项列表 -->
    <transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute z-50 mt-1 w-full bg-white rounded-xl border border-gray-200 shadow-lg max-h-60 overflow-auto custom-scrollbar"
      >
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          @click="selectOption(option.value)"
          :class="[
            'w-full text-left px-4 py-3 text-sm transition-colors',
            'first:rounded-t-xl last:rounded-b-xl',
            modelValue === option.value
              ? 'bg-gray-100 text-gray-900 font-medium'
              : 'text-gray-700 hover:bg-gray-50'
          ]"
        >
          {{ option.label }}
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";

interface Option {
  label: string;
  value: string;
}

const props = withDefaults(
  defineProps<{
    modelValue: string;
    options: Option[];
    placeholder?: string;
  }>(),
  {
    placeholder: "请选择"
  }
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const isOpen = ref(false);
const selectRef = ref<HTMLElement | null>(null);

const displayText = computed(() => {
  const option = props.options.find((opt) => opt.value === props.modelValue);
  return option ? option.label : "";
});

const toggleDropdown = () => {
  isOpen.value = !isOpen.value;
};

const selectOption = (value: string) => {
  emit("update:modelValue", value);
  isOpen.value = false;
};

// 点击外部关闭下拉框
const handleClickOutside = (event: MouseEvent) => {
  if (selectRef.value && !selectRef.value.contains(event.target as Node)) {
    isOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped>
.input {
  @apply w-full rounded-xl border border-gray-200 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm;
}

/* 自定义滚动条样式 - 极简风格 */
.custom-scrollbar {
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent; /* Firefox: 滑块颜色 轨道颜色 */
}

/* Webkit 浏览器 (Chrome, Safari, Edge) */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px; /* 滚动条宽度 */
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent; /* 滚动条轨道背景透明 */
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5); /* 滚动条滑块颜色 - 浅灰色 */
  border-radius: 3px;
  border: none; /* 移除边框 */
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7); /* 悬停时稍深一点 */
}

/* 隐藏滚动条按钮（上下箭头） */
.custom-scrollbar::-webkit-scrollbar-button {
  display: none; /* 不显示上下箭头按钮 */
}
</style>

