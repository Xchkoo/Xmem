<template>
  <div>
    <!-- 第一行：消费金额 货币 | 商家 | 分类 -->
    <div class="flex justify-between items-center mb-2">
      <div class="font-semibold text-lg">
        <span v-if="ledger.status === 'pending' || ledger.status === 'processing'">待识别</span>
        <span v-else>
          {{ ledger.amount ?? "待识别" }} 
          <span class="text-sm text-gray-500">{{ ledger.currency }}</span>
        </span>
      </div>
      <div class="text-sm text-gray-500 flex items-center gap-2">
        <span v-if="ledger.status === 'pending' || ledger.status === 'processing'" class="text-blue-500 flex items-center gap-1">
          <span v-if="ledger.status === 'pending'" class="animate-pulse">⏳</span>
          <span v-else class="animate-spin">🔄</span>
          {{ ledger.status === 'pending' ? '等待中' : '识别中...' }}
        </span>
        <span v-else-if="ledger.status === 'failed'" class="text-red-500">识别失败</span>
        <template v-else>
          <span v-if="ledger.merchant" class="text-gray-600">{{ ledger.merchant }}</span>
          <span v-if="ledger.merchant && ledger.category" class="text-gray-400">|</span>
          <span>{{ ledger.category || "未分类" }}</span>
        </template>
      </div>
    </div>
    
    <!-- 第二行：原始文本（如果过长则截断） -->
    <p class="text-gray-700 mt-1 text-sm line-clamp-2">
      {{ truncatedText }}
    </p>
    
    <!-- 第三行：时间 | 状态 -->
    <div class="flex justify-between items-center mt-2">
      <div class="text-xs text-gray-400">{{ formatTime(ledger.event_time || ledger.created_at) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { LedgerEntry } from "../stores/data";

const props = defineProps<{
  ledger: LedgerEntry;
}>();

const MAX_TEXT_LENGTH = 100; // 最大文本长度

const truncatedText = computed(() => {
  const text = props.ledger.raw_text || (props.ledger.status === 'pending' || props.ledger.status === 'processing' ? '正在处理中，请稍候...' : '');
  if (text.length <= MAX_TEXT_LENGTH) {
    return text;
  }
  return text.substring(0, MAX_TEXT_LENGTH) + '……';
});

const formatTime = (time: string) => {
  const date = new Date(time);
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

