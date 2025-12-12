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
        <div class="text-xl font-bold">查看记账</div>
      </div>
      <button
        v-if="ledger && ledger.status === 'completed'"
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
      <div v-if="ledger" class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <!-- Ledger 详情 -->
        <div class="space-y-6">
          <!-- 金额和状态 -->
          <div class="flex justify-between items-center">
            <div>
              <div class="font-semibold text-2xl">
                <span v-if="ledger.status === 'pending' || ledger.status === 'processing'">待识别</span>
                <span v-else>
                  {{ ledger.amount ?? "待识别" }} 
                  <span class="text-lg text-gray-500">{{ ledger.currency }}</span>
                </span>
              </div>
            </div>
            <div>
              <span v-if="ledger.status === 'pending' || ledger.status === 'processing'" class="text-blue-500 flex items-center gap-1">
                <span v-if="ledger.status === 'pending'" class="animate-pulse">⏳</span>
                <span v-else class="animate-spin">🔄</span>
                {{ ledger.status === 'pending' ? '等待中' : '识别中...' }}
              </span>
              <span v-else-if="ledger.status === 'failed'" class="text-red-500">识别失败</span>
            </div>
          </div>

          <!-- 分类和商家 -->
          <div v-if="ledger.status === 'completed'" class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-600 mb-1">分类</label>
              <div class="text-gray-900 font-medium">{{ ledger.category || "未分类" }}</div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">商家</label>
              <div class="text-gray-900 font-medium">{{ ledger.merchant || "未知" }}</div>
            </div>
          </div>

          <!-- 原始文本 -->
          <div>
            <label class="block text-sm text-gray-600 mb-2">原始文本</label>
            <div class="bg-primary rounded-2xl p-4 text-gray-800 whitespace-pre-wrap">
              {{ ledger.raw_text || (ledger.status === 'pending' || ledger.status === 'processing' ? '正在处理中，请稍候...' : '') }}
            </div>
          </div>

          <!-- 时间信息 -->
          <div class="border-t pt-4 flex items-center justify-between">
            <div class="text-xs text-gray-400">
              创建时间：{{ formatTime(ledger.created_at) }}
            </div>
            <div v-if="ledger.updated_at && ledger.updated_at !== ledger.created_at" class="text-xs text-gray-400">
              更新时间：{{ formatTime(ledger.updated_at) }}
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-12">
        <p class="text-gray-400">加载中...</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useDataStore } from "../stores/data";
import type { LedgerEntry } from "../stores/data";

const props = defineProps<{
  ledgerId: number;
}>();

const emit = defineEmits<{
  back: [];
  edit: [];
}>();

const data = useDataStore();

// 使用 computed 从 store 中获取 ledger，这样会自动响应 store 的变化
const ledger = computed<LedgerEntry | null>(() => {
  const found = data.ledgers.find(l => l.id === props.ledgerId);
  return found || null;
});

// 如果 store 中没有，尝试从 API 获取
onMounted(async () => {
  if (!ledger.value) {
    try {
      await data.fetchLedgerStatus(props.ledgerId);
    } catch (error) {
      console.error("获取 ledger 失败:", error);
    }
  }
});

const formatTime = (time: string) => {
  const date = new Date(time);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
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

