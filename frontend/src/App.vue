<template>
  <!-- 未登录时显示登录注册页面 -->
  <Auth v-if="!user.token" />
  
  <!-- 已登录时显示主界面 -->
  <div v-else class="min-h-screen bg-primary text-gray-900 flex flex-col items-center">
    <header class="w-full max-w-4xl px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="text-xl font-bold">Xmem 个人记账 + 待办</div>
      <div class="flex items-center gap-3 text-sm">
        <span class="text-gray-600">你好，{{ user.profile?.email }}</span>
        <button class="btn ghost" @click="user.logout()">退出</button>
      </div>
    </header>

    <main class="w-full max-w-4xl px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <TabSwitcher v-model="currentTab" :tabs="tabs" />
        </div>

        <div class="space-y-6">
          <div class="bg-primary rounded-2xl p-4 md:p-6 shadow-inner">
            <label class="block text-gray-600 text-sm mb-2">快速输入</label>
            <textarea
              v-model="inputText"
              class="input h-32 md:h-40"
              placeholder="贴上文字或描述，自动按当前分页归类"
            />
            <div class="flex flex-wrap justify-between items-center gap-3 mt-3">
              <div class="flex gap-3">
                <label class="btn ghost cursor-pointer">
                  📎 选择文件
                  <input type="file" @change="onFile" class="hidden" />
                </label>
                <button class="btn ghost" @click="pasteFromClipboard">📋 粘贴</button>
              </div>
              <div class="flex gap-3">
                <button class="btn ghost" @click="inputText = ''">清空</button>
                <button class="btn primary" @click="handleSubmit">提交到 {{ currentLabel }}</button>
              </div>
            </div>
          </div>

          <div class="grid md:grid-cols-2 gap-4">
            <div>
              <div class="section-title">最新笔记</div>
              <div class="space-y-3">
                <div v-for="note in data.notes.slice(0, 4)" :key="note.id" class="card">
                  <div class="text-gray-800 whitespace-pre-line">{{ note.body }}</div>
                  <div class="text-xs text-gray-400 mt-2">{{ formatTime(note.created_at) }}</div>
                </div>
                <p v-if="!data.notes.length" class="text-gray-400 text-sm">暂无笔记</p>
              </div>
            </div>
            <div>
              <div class="section-title">最新记账</div>
              <div class="space-y-3">
                <div v-for="item in data.ledgers.slice(0, 4)" :key="item.id" class="card">
                  <div class="flex justify-between items-center">
                    <div class="font-semibold text-lg">
                      {{ item.amount ?? "待识别" }} <span class="text-sm text-gray-500">{{ item.currency }}</span>
                    </div>
                    <div class="text-sm text-gray-500">{{ item.category || "未分类" }}</div>
                  </div>
                  <p class="text-gray-700 mt-1">{{ item.raw_text }}</p>
                  <div class="text-xs text-gray-400 mt-2">{{ formatTime(item.created_at) }}</div>
                </div>
                <p v-if="!data.ledgers.length" class="text-gray-400 text-sm">暂无记账</p>
              </div>
            </div>
          </div>

          <div>
            <div class="section-title">待办事项</div>
            <div class="bg-primary rounded-2xl p-4 shadow-inner flex flex-col gap-3">
              <div class="flex gap-2">
                <input v-model="todoText" class="input flex-1" placeholder="添加待办..." />
                <button class="btn primary" @click="addTodo">添加</button>
              </div>
              <div class="space-y-2">
                <label
                  v-for="todo in data.todos"
                  :key="todo.id"
                  class="flex items-center justify-between bg-white px-3 py-2 rounded-xl shadow"
                >
                  <div class="flex items-center gap-3">
                    <input type="checkbox" :checked="todo.completed" @change="data.toggleTodo(todo.id)" />
                    <span :class="{ 'line-through text-gray-400': todo.completed }">{{ todo.title }}</span>
                  </div>
                  <button class="text-gray-400 hover:text-red-500" @click="data.removeTodo(todo.id)">删除</button>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <FabMenu @settings="openSettings" @notes="scrollToSection('notes')" @ledger="scrollToSection('ledger')" />
    
    <!-- 设置界面 -->
    <Settings :visible="showSettings" @close="showSettings = false" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import TabSwitcher from "./components/TabSwitcher.vue";
import FabMenu from "./components/FabMenu.vue";
import Auth from "./components/Auth.vue";
import Settings from "./components/Settings.vue";
import { useUserStore } from "./stores/user";
import { useDataStore } from "./stores/data";

const tabs = [
  { label: "笔记模式", value: "note" },
  { label: "记账模式", value: "ledger" }
];
const currentTab = ref<"note" | "ledger">("note");
const inputText = ref("");
const todoText = ref("");
const showSettings = ref(false);

const user = useUserStore();
const data = useDataStore();

const currentLabel = computed(() => (currentTab.value === "note" ? "笔记库" : "记账"));

onMounted(async () => {
  if (user.token) {
    await user.fetchProfile();
    await data.loadAll();
  }
});

const handleSubmit = async () => {
  if (!inputText.value.trim()) return;
  if (currentTab.value === "note") {
    await data.addNote(inputText.value);
  } else {
    await data.addLedger(inputText.value);
  }
  inputText.value = "";
};

const addTodo = async () => {
  if (!todoText.value.trim()) return;
  await data.addTodo(todoText.value);
  todoText.value = "";
};

const onFile = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  inputText.value = `${inputText.value}\n[附件] ${file.name}`.trim();
};

const pasteFromClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      inputText.value = inputText.value ? `${inputText.value}\n${text}` : text;
    }
  } catch (err) {
    console.error("读取剪切板失败:", err);
    alert("无法读取剪切板，请确保已授予剪切板访问权限");
  }
};

const scrollToSection = (type: "notes" | "ledger") => {
  // 简单滚动示意，需结合实际标记
  window.scrollTo({ top: 200, behavior: "smooth" });
};

const openSettings = () => {
  showSettings.value = true;
};

const formatTime = (timeStr: string) => {
  if (!timeStr) return "";
  const date = new Date(timeStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) {
    return "刚刚";
  } else if (minutes < 60) {
    return `${minutes}分钟前`;
  } else if (hours < 24) {
    return `${hours}小时前`;
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    
    if (year === now.getFullYear()) {
      return `${month}-${day} ${hour}:${minute}`;
    } else {
      return `${year}-${month}-${day} ${hour}:${minute}`;
    }
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
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}
.card {
  @apply bg-white p-4 rounded-xl shadow;
}
.section-title {
  @apply text-sm font-semibold text-gray-500 mb-2;
}
.shadow-inner {
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.03), 0 6px 20px rgba(0, 0, 0, 0.05);
}
</style>

