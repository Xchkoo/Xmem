<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="$emit('back')"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">查看笔记</div>
      </div>
      <button
        @click="$emit('edit')"
        class="btn primary flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        编辑
      </button>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div v-if="note" class="bg-white rounded-3xl shadow-float p-4 md:p-6 lg:p-8 mx-auto">
        <!-- 笔记内容 -->
        <div class="mb-6" @dblclick="$emit('edit')">
           <MdPreview v-secure-display :modelValue="note.body_md || ''" />
        </div>

        <!-- 笔记信息 -->
        <div class="border-t pt-4 flex items-center justify-between">
          <div class="text-xs text-gray-400">
            创建时间：{{ formatTime(note.created_at) }}
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="copyNoteText"
              class="btn ghost text-sm"
              title="复制文本"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              复制
            </button>
            <button
              @click="handleDelete"
              class="btn ghost text-sm text-red-500 hover:text-red-700"
              title="删除笔记"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              删除
            </button>
          </div>
        </div>
      </div>
      <div v-else class="bg-white rounded-3xl shadow-float p-4 md:p-6 lg:p-8 mx-auto text-center">
        <p class="text-gray-400 text-lg">笔记不存在</p>
      </div>
    </main>
    
    <!-- 确认对话框 -->
    <ConfirmDialog
      :visible="confirm.visible"
      :title="confirm.title"
      :message="confirm.message"
      :confirm-text="confirm.confirmText"
      :cancel-text="confirm.cancelText"
      :type="confirm.type"
      @confirm="confirm.confirm()"
      @cancel="confirm.cancel()"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { useConfirmStore } from "../stores/confirm";
import ConfirmDialog from "./ConfirmDialog.vue";

interface Props {
  noteId: number | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  back: [];
  edit: [];
  deleted: [];
}>();

const data = useDataStore();
const toast = useToastStore();
const confirm = useConfirmStore();

const note = computed(() => {
  if (!props.noteId) return null;
  return data.notes.find(n => n.id === props.noteId);
});

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr);
  return date.toLocaleString();
};

// 复制笔记文本
const copyNoteText = async () => {
  if (!note.value || !note.value.body_md) return;
  
  try {
    await navigator.clipboard.writeText(note.value.body_md);
    toast.success("已复制到剪贴板");
  } catch (err) {
    console.error("复制失败:", err);
    toast.error("复制失败，请手动复制");
  }
};

// 删除笔记
const handleDelete = () => {
  if (!props.noteId) return;
  
  confirm.show({
    title: "删除笔记",
    message: "确定要删除这条笔记吗？此操作无法撤销。",
    confirmText: "删除",
    type: "danger"
  }).then(async (result) => {
    if (result) {
      try {
        await data.removeNote(props.noteId!);
        toast.success("笔记删除成功");
        emit("deleted");
      } catch (error: any) {
        console.error("删除笔记失败:", error);
        toast.error(error.response?.data?.detail || "笔记删除失败，请重试");
      }
    }
  });
};
</script>

<style scoped>
/* 修复图片在没有 alt 文本时可能不显示的问题 */
:deep(.md-editor-preview img) {
  display: inline-block;
  max-width: 100%;
  min-height: 20px; /* 确保即使加载失败也有高度 */
  background-color: transparent;
}

.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
</style>
