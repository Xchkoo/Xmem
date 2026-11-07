<template>
  <div class="min-h-screen bg-bg text-text">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="handleBack"
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
        @click="ledgerEditor.open(ledger)"
        class="btn primary flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        编辑
      </button>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div v-if="ledger" class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
        <!-- Ledger 详情 -->
        <div class="space-y-6">
          <!-- 原始截图：记账的"证据"，永久保留 -->
          <div v-if="imageUrl" class="space-y-2">
            <div class="text-sm text-muted">原始图片</div>
            <img
              :src="imageUrl"
              alt="记账原图"
              class="w-full max-h-96 object-contain rounded-2xl border border-border bg-surface2 cursor-zoom-in"
              @click="previewOpen = true"
            />
          </div>
          <!-- 金额和状态 -->
          <div class="flex justify-between items-center">
            <div>
              <div class="font-semibold text-2xl">
                <span v-if="ledger.status === 'pending' || ledger.status === 'processing'">待识别</span>
                <span v-else>
                  {{ ledger.amount ?? "待识别" }} 
                  <span class="text-lg text-muted">{{ ledger.currency }}</span>
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
              <label class="block text-sm text-muted mb-1">分类</label>
              <div class="text-text font-medium">{{ ledger.category || "未分类" }}</div>
            </div>
            <div>
              <label class="block text-sm text-muted mb-1">商家</label>
              <div class="text-text font-medium">{{ ledger.merchant || "未知" }}</div>
            </div>
          </div>

          <!-- 原始文本 -->
          <div>
            <label class="block text-sm text-muted mb-2">原始文本</label>
            <div class="bg-primary rounded-2xl p-4 text-text whitespace-pre-wrap border border-border shadow-inset">
              {{ ledger.raw_text || (ledger.status === 'pending' || ledger.status === 'processing' ? '正在处理中，请稍候...' : '') }}
            </div>
          </div>

          <!-- 时间信息 -->
          <div class="border-t border-border pt-4 flex items-center justify-between">
            <div class="text-xs text-muted">
              {{ ledger.event_time ? '记账时间：' : '创建时间：' }}{{ formatTime(ledger.event_time || ledger.created_at) }}
            </div>
            <div v-if="ledger.updated_at && ledger.updated_at !== ledger.created_at" class="text-xs text-muted">
              更新时间：{{ formatTime(ledger.updated_at) }}
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-12">
        <p class="text-muted">加载中...</p>
      </div>
    </main>

    <!-- 大图预览 -->
    <div
      v-if="previewOpen && imageUrl"
      class="fixed inset-0 z-[120] bg-black/90 flex items-center justify-center p-4"
      @click="previewOpen = false"
    >
      <img :src="imageUrl" alt="记账原图" class="max-w-full max-h-full object-contain" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useDataStore } from "../stores/data";
import { useLedgerEditorStore } from "../stores/ledgerEditor";
import { useAuthedImage } from "../utils/authedImage";

const props = defineProps<{
  ledgerId: number | string;
}>();

const router = useRouter();
const data = useDataStore();
const ledgerEditor = useLedgerEditorStore();
const handleBack = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.push({ name: "home" });
};

const ledger = computed(() => {
  const id = Number(props.ledgerId);
  return data.ledgers.find((l) => l.id === id);
});

const imageUrl = useAuthedImage(computed(() => ledger.value?.image_url));
const previewOpen = ref(false);

// 如果 store 中没有，尝试从 API 获取
onMounted(async () => {
  if (!ledger.value) {
    try {
      await data.fetchLedgerStatus(Number(props.ledgerId));
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
  @apply bg-accent text-on-accent shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70;
}
</style>

