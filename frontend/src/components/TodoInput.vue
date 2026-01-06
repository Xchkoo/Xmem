<template>
  <div class="flex gap-2">
    <div class="flex-1 relative">
      <input 
        v-model="text"
        @keydown.enter.prevent="handleEnter"
        class="input flex-1 pr-12" 
        :placeholder="placeholder"
        maxlength="50"
      />
      <span 
        class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none"
        :class="{ 'text-red-500': text.length > 50 }"
      >
        {{ text.length }}/50
      </span>
    </div>
    <button 
      class="btn primary" 
      @click="handleAdd"
      :disabled="text.length > 50"
    >
      添加
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";

const data = useDataStore();
const toast = useToastStore();

const text = ref("");
const creatingGroup = ref(false);
const windowWidth = ref(typeof window !== "undefined" ? window.innerWidth : 1024);

const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

const placeholder = computed(() => {
  return windowWidth.value < 640 ? "添加待办..." : "添加待办...（按回车创建组）";
});

onMounted(() => {
  if (typeof window !== "undefined") {
    window.addEventListener("resize", handleResize);
    windowWidth.value = window.innerWidth;
  }
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", handleResize);
  }
});

const handleAdd = async () => {
  if (!text.value.trim()) {
    toast.warning("待办内容不能为空");
    return;
  }
  
  if (text.value.length > 50) {
    toast.warning("待办事项不能超过50字");
    return;
  }
  
  try {
    await data.addTodo(text.value);
    text.value = "";
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "添加失败");
  }
};

const handleEnter = async () => {
  if (!text.value.trim()) return;
  if (creatingGroup.value) return;
  
  creatingGroup.value = true;
  try {
    const title = text.value.trim();
    text.value = "";
    
    // 创建组标题
    const group = await data.addTodo(title);
    
    // 创建组的第一个待办（使用默认标题）
    const firstItem = await data.addTodo("新建待办", group.id);
    
    // 等待 DOM 更新后，聚焦到第一个待办的输入框
    await nextTick();
    // 通过事件通知 TodoGroup 组件聚焦第一个待办
    const event = new CustomEvent('focus-first-item', { detail: { groupId: group.id } });
    window.dispatchEvent(event);
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "创建失败");
  } finally {
    creatingGroup.value = false;
  }
};
</script>

<style scoped>
.input {
  @apply w-full rounded-xl border border-gray-200 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm;
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95;
}
</style>
