<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-4xl md:max-w-7xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="$emit('cancel')"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">{{ props.noteId ? '编辑笔记' : '添加新笔记' }}</div>
      </div>
      <button
        @click="handleSave"
        class="btn ghost flex items-center gap-2"
        :disabled="!content.trim() || saving"
      >
        {{ saving ? "保存中..." : "保存" }}
      </button>
    </header>

    <main class="w-full max-w-4xl md:max-w-7xl mx-auto px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <!-- 编辑器工具栏 -->
        <div class="flex flex-wrap gap-2 mb-4 p-3 bg-gray-50 rounded-xl">
          <button @click="insertMarkdown('**', '**')" class="toolbar-btn" title="粗体">B</button>
          <button @click="insertMarkdown('*', '*')" class="toolbar-btn" title="斜体">I</button>
          <button @click="insertMarkdown('`', '`')" class="toolbar-btn" title="代码">&lt;/&gt;</button>
          <button @click="insertMarkdown('# ', '')" class="toolbar-btn" title="标题">H</button>
          <button @click="insertMarkdown('- ', '')" class="toolbar-btn" title="列表">•</button>
          <button @click="insertMarkdown('> ', '')" class="toolbar-btn" title="引用">&gt;</button>
          <div class="flex-1"></div>
          <label class="toolbar-btn cursor-pointer">
            📷 插入图片
            <input type="file" accept="image/*" multiple @change="handleImageUpload" class="hidden" />
          </label>
          <label class="toolbar-btn cursor-pointer">
            📎 插入文件
            <input type="file" multiple @change="handleFileUpload" class="hidden" />
          </label>
        </div>

        <!-- Markdown 快捷键提示 -->
        <div class="mb-4 p-3 bg-blue-50 rounded-xl text-xs text-gray-600">
          <div class="font-semibold mb-2">Markdown 快捷键：</div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div><code>**文本**</code> - 粗体</div>
            <div><code>*文本*</code> - 斜体</div>
            <div><code>`代码`</code> - 代码</div>
            <div><code># 标题</code> - 标题</div>
            <div><code>- 列表</code> - 无序列表</div>
            <div><code>> 引用</code> - 引用</div>
            <div><code>[链接](url)</code> - 链接</div>
            <div><code>![图片](url)</code> - 图片</div>
          </div>
        </div>

        <!-- 编辑器与预览区域：桌面视图左右布局，移动端上下布局 -->
        <div class="flex flex-col md:flex-row gap-4">
          <!-- 编辑器区域：固定占50%宽度 -->
          <div class="w-full md:w-1/2 md:flex-[0_0_50%] mb-4 md:mb-0 flex flex-col">
            <div class="text-sm font-semibold text-gray-500 mb-2">编辑：</div>
          <textarea
            v-model="content"
            ref="editorRef"
              class="w-full h-96 md:min-h-[400px] md:h-[calc(100vh-350px)] p-4 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 font-mono text-sm resize-none flex-1"
            placeholder="开始编写你的笔记...支持 Markdown 语法"
          />
        </div>

          <!-- 预览区域：固定占50%宽度 -->
          <div class="w-full md:w-1/2 md:flex-[0_0_50%] mb-4 md:mb-0 flex flex-col">
          <div class="text-sm font-semibold text-gray-500 mb-2">预览：</div>
          <div 
              class="prose max-w-none p-4 bg-gray-50 rounded-xl min-h-[200px] md:min-h-[400px] md:h-[calc(100vh-350px)] overflow-y-auto border border-gray-200 flex-1"
              v-html="previewContent"
          />
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { marked } from "marked";
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";

interface FileInfo {
  name: string;
  url: string;
  size: number;
}

interface Props {
  noteId?: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  noteId: null
});

const emit = defineEmits<{
  cancel: [];
  saved: [];
}>();

const data = useDataStore();
const toast = useToastStore();
const content = ref("");
const editorRef = ref<HTMLTextAreaElement | null>(null);
const saving = ref(false);

// 渲染 Markdown
const renderedMarkdown = computed(() => {
  if (!content.value || !content.value.trim()) return "";
  try {
  return marked(content.value);
  } catch (error) {
    console.error("Markdown 渲染错误:", error);
    return '<p class="text-red-500">渲染错误，请检查 Markdown 语法</p>';
  }
});

// 预览区域显示内容
const previewContent = computed(() => {
  if (!content.value || !content.value.trim()) {
    return '<p class="text-gray-400 italic">预览将在这里显示...</p>';
  }
  const rendered = renderedMarkdown.value;
  if (!rendered || rendered.trim() === "") {
    return '<p class="text-gray-400 italic">预览将在这里显示...</p>';
  }
  return rendered;
});

// 插入 Markdown 语法
const insertMarkdown = (before: string, after: string) => {
  if (!editorRef.value) return;
  const textarea = editorRef.value;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selectedText = content.value.substring(start, end);
  const newText = before + selectedText + after;
  content.value = content.value.substring(0, start) + newText + content.value.substring(end);
  
  // 恢复光标位置
  nextTick(() => {
    textarea.focus();
    textarea.setSelectionRange(start + before.length, start + before.length + selectedText.length);
  });
};

// 处理图片上传
const handleImageUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  for (const file of Array.from(files)) {
    try {
      const url = await data.uploadImage(file);
      // 在光标位置插入图片
      insertImageMarkdown(url);
    } catch (err: any) {
      toast.error(err.message || "图片上传失败");
    }
  }
};

// 处理文件上传
const handleFileUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  for (const file of Array.from(files)) {
    try {
      const fileInfo = await data.uploadFile(file);
      // 在光标位置插入文件链接
      insertFileMarkdown(fileInfo);
    } catch (err: any) {
      toast.error(err.message || "文件上传失败");
    }
  }
};

// 插入图片 Markdown
const insertImageMarkdown = (url: string) => {
  if (!editorRef.value) return;
  const textarea = editorRef.value;
  const start = textarea.selectionStart;
  const markdown = `![图片](${url})\n`;
  content.value = content.value.substring(0, start) + markdown + content.value.substring(start);
  nextTick(() => {
    textarea.focus();
    textarea.setSelectionRange(start + markdown.length, start + markdown.length);
  });
};

// 插入文件 Markdown
const insertFileMarkdown = (fileInfo: FileInfo) => {
  if (!editorRef.value) return;
  const textarea = editorRef.value;
  const start = textarea.selectionStart;
  // 确保URL是完整的
  const apiUrl = (import.meta as any).env?.VITE_API_URL || "/api";
  const fullUrl = fileInfo.url.startsWith("http") ? fileInfo.url : `${apiUrl}${fileInfo.url}`;
  const markdown = `[${fileInfo.name}](${fullUrl})\n`;
  content.value = content.value.substring(0, start) + markdown + content.value.substring(start);
  nextTick(() => {
    textarea.focus();
    textarea.setSelectionRange(start + markdown.length, start + markdown.length);
  });
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
  if (!content.value.trim()) return;
  
  saving.value = true;
  try {
    if (props.noteId) {
      // 更新已有笔记
      await data.updateNote(props.noteId, content.value);
    } else {
      // 创建新笔记
      await data.addNoteWithMD(content.value);
      // 如果是新建笔记，清空 localStorage 中的快速输入内容（因为已经导入并保存了）
      if (typeof window !== "undefined") {
        localStorage.removeItem("quickInputText");
      }
    }
    emit("saved");
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

.toolbar-btn {
  @apply px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-semibold hover:bg-gray-50 transition-colors;
}

.prose {
  @apply text-gray-800;
}

.prose :deep(h1) {
  @apply text-2xl font-bold mt-4 mb-2;
}

.prose :deep(h2) {
  @apply text-xl font-bold mt-3 mb-2;
}

.prose :deep(h3) {
  @apply text-lg font-bold mt-2 mb-1;
}

.prose :deep(p) {
  @apply mb-2;
}

.prose :deep(ul), .prose :deep(ol) {
  @apply list-disc list-inside mb-2;
}

.prose :deep(code) {
  @apply bg-gray-200 px-1 rounded text-sm;
}

.prose :deep(pre) {
  @apply bg-gray-100 p-2 rounded mb-2 overflow-x-auto;
}

.prose :deep(blockquote) {
  @apply border-l-4 border-gray-300 pl-4 italic my-2;
}

.prose :deep(a) {
  @apply text-blue-600 hover:underline;
}

.prose :deep(img) {
  @apply max-w-full rounded my-2;
}
</style>

