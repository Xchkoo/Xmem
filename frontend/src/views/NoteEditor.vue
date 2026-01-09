<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-4xl md:max-w-7xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="router.back()"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">{{ props.noteId ? '编辑笔记' : '添加新笔记' }}</div>
      </div>
      
      <div class="flex items-center gap-2">
        <button
          @click="handleSave"
          class="btn ghost flex items-center gap-2"
          :disabled="!content.trim() || saving"
        >
          {{ saving ? "保存中..." : "保存" }}
        </button>
      </div>
    </header>

    <main class="w-full max-w-4xl md:max-w-7xl mx-auto px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <MdEditor 
          v-secure-display
          v-model="content" 
          @onUploadImg="onUploadImg"
          class="min-h-[600px] rounded-xl overflow-hidden border border-gray-200"
          :toolbars="toolbars"
          :toolbarsExclude="['github']"
        >
          <template #defToolbars>
            <NormalToolbar title="插入文件" @click="triggerFileUpload">
              <template #trigger>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </template>
            </NormalToolbar>
          </template>
        </MdEditor>
        <!-- 隐藏的文件输入框 -->
        <input ref="fileInput" type="file" multiple @change="handleFileUpload" class="hidden" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { MdEditor, NormalToolbar, type ToolbarNames } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";

interface Props {
  noteId?: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  noteId: null
});


const router = useRouter();
const data = useDataStore();
const toast = useToastStore();
const content = ref("");
const saving = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

// 自定义工具栏配置
const toolbars: ToolbarNames[] = [
  'bold',
  'underline',
  'italic',
  '-',
  'title',
  'strikeThrough',
  'sub',
  'sup',
  'quote',
  'unorderedList',
  'orderedList',
  'task',
  '-',
  'codeRow',
  'code',
  'link',
  'image',
  0, // 自定义工具栏位置：上传文件
  'table',
  'mermaid',
  'katex',
  '-',
  'revoke',
  'next',
  '=',
  'pageFullscreen',
  'fullscreen',
  'preview',
  'catalog',
];

// 触发文件选择
const triggerFileUpload = () => {
  fileInput.value?.click();
};

// 处理文件上传
const handleFileUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files || files.length === 0) return;
  
  for (const file of Array.from(files)) {
    try {
      const fileInfo = await data.uploadFile(file);
      // 插入文件链接到 Markdown 内容
      const fileLink = `[${fileInfo.name}](${fileInfo.url})`;
      
      // 在光标位置插入（如果支持）或者追加
      // 这里简单追加或插入到最后，MdEditor 提供了 insert 方法但我们需要 ref
      // 简单起见，我们直接追加到末尾，或者尝试寻找 better way
      // MdEditor 的 modelValue 是双向绑定的，直接修改 content 即可
      // 但最好是插入到光标处。MdEditor 实例 exposed insert 方法
      // 暂时追加到新行
      content.value = content.value ? `${content.value}\n${fileLink}` : fileLink;
      
    } catch (err: any) {
      toast.error(err.message || "文件上传失败");
    }
  }
  
  // 清空文件输入
  (e.target as HTMLInputElement).value = "";
};

// 处理图片上传
const onUploadImg = async (files: File[], callback: (urls: string[]) => void) => {
  const urls: string[] = [];
  for (const file of files) {
    try {
      const url = await data.uploadImage(file);
      urls.push(url);
    } catch (err: any) {
      toast.error(err.message || "图片上传失败");
    }
  }
  callback(urls);
};

// 加载笔记内容（编辑模式）
const loadNoteContent = async () => {
  if (!props.noteId) {
    // 新建模式：从 localStorage 加载快速输入内容
    if (typeof window !== "undefined") {
      const quickInputText = localStorage.getItem("quickInputText");
      if (quickInputText) {
        content.value = quickInputText;
        // 加载后清空 localStorage 中的快速输入内容
        localStorage.removeItem("quickInputText");
      } else {
        content.value = "";
      }
    } else {
      content.value = "";
    }
    return;
  }

  try {
    // 确保笔记列表已加载
    if (data.notes.length === 0) {
      await data.fetchNotes();
    }

    // 查找要编辑的笔记
    const note = data.notes.find(n => n.id === props.noteId);
    if (note) {
      // 加载笔记内容（编辑模式，不从快速输入加载）
      content.value = note.body_md || "";
    } else {
      // 笔记不存在，清空内容
      content.value = "";
    }
  } catch (err: any) {
    console.error("加载笔记内容失败:", err);
    // 如果加载失败，至少清空编辑器
    content.value = "";
  }
};

// 组件挂载时加载笔记内容
onMounted(() => {
  loadNoteContent();
});

// 监听 noteId 变化，重新加载内容
watch(() => props.noteId, () => {
  loadNoteContent();
});

// 保存笔记
const handleSave = async () => {
  // 检查内容是否为空
  if (!content.value.trim()) return;
  
  saving.value = true;
  try {
    if (props.noteId) {
      const id = Number(props.noteId);
      await data.updateNote(id, content.value);
      toast.success("保存成功");
    } else {
      await data.addNoteWithMD(content.value);
      toast.success("创建成功");
      // 清除快速输入缓存
      if (typeof window !== "undefined") {
        localStorage.removeItem("quickInputText");
      }
    }
    router.back();
  } catch (err: any) {
    toast.error(err.message || "保存失败");
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
</style>
