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
        <div class="text-xl font-bold">记账库</div>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div class="bg-white rounded-3xl shadow-float p-6 md:p-8">
        <!-- 筛选区域 -->
        <div class="mb-6">
          <CustomSelect
            v-model="selectedCategory"
            :options="categoryOptions"
            placeholder="全部分类"
            class="w-full md:w-auto"
          >
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
            </template>
          </CustomSelect>
        </div>

        <!-- Ledger 列表 -->
        <div v-if="data.ledgers.length" class="space-y-4">
          <template v-for="(group, date) in groupedLedgers" :key="date">
            <!-- 日期分割线 -->
            <div class="flex items-center gap-4 my-6">
              <div class="flex-1 border-t border-gray-300"></div>
              <div class="text-sm font-semibold text-gray-500 px-3">{{ date }}</div>
              <div class="flex-1 border-t border-gray-300"></div>
            </div>
            <!-- 该日期的 ledger 列表 -->
            <div class="space-y-3">
              <div
                v-for="ledger in group"
                :key="ledger.id"
                class="card relative group hover:shadow-lg transition-all duration-200 cursor-pointer"
                :class="{ 
                  'opacity-60': ledger.status === 'pending' || ledger.status === 'processing',
                  'border-2 border-blue-300 border-dashed': ledger.status === 'pending' || ledger.status === 'processing'
                }"
                @click="handleLedgerClick(ledger.id)"
              >
                <!-- Ledger 内容 -->
                <LedgerCardContent :ledger="ledger" />
                
                <!-- 操作按钮（右下角） -->
                <div class="absolute bottom-2 right-2 flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                  <button
                    v-if="ledger.status === 'completed'"
                    @click.stop="handleEdit(ledger)"
                    class="text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-50 active:scale-95"
                    title="编辑"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    @click.stop="handleDelete(ledger.id)"
                    class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
                    title="删除"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </template>
        </div>
        <div v-else class="text-center py-12">
          <p class="text-gray-400 text-lg">还没有记账</p>
          <p class="text-gray-400 text-sm mt-2">在主界面添加你的第一条记账吧</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useDataStore } from "../stores/data";
import { useConfirmStore } from "../stores/confirm";
import { useToastStore } from "../stores/toast";
import LedgerCardContent from "./LedgerCardContent.vue";
import CustomSelect from "./CustomSelect.vue";
import type { LedgerEntry } from "../stores/data";

// 固定的分类列表
const categories = [
  "餐饮美食",
  "服装装扮",
  "日用百货",
  "家居家装",
  "数码电器",
  "运动户外",
  "美容美发",
  "母婴亲子",
  "宠物",
  "交通出行",
  "爱车养车",
  "住房物业",
  "酒店旅游",
  "文化休闲",
  "教育培训",
  "医疗健康",
  "生活服务",
  "公共服务",
  "商业服务",
  "公益捐赠",
  "互助保障",
  "投资理财",
  "保险",
  "信用借还",
  "充值缴费",
  "其他"
];

const selectedCategory = ref("");

// 转换为选项格式
const categoryOptions = computed(() => [
  { value: "", label: "全部分类" },
  ...categories.map(cat => ({ value: cat, label: cat }))
]);

const emit = defineEmits<{
  back: [];
  "view-ledger": [ledgerId: number];
  "edit-ledger": [ledger: LedgerEntry];
  settings: [];
  notes: [];
  ledger: [];
}>();

const data = useDataStore();
const confirm = useConfirmStore();
const toast = useToastStore();

// 按日期分组 ledger
const groupedLedgers = computed(() => {
  const groups: Record<string, LedgerEntry[]> = {};
  data.ledgers.forEach(ledger => {
    const date = new Date(ledger.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(ledger);
  });
  return groups;
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

const handleLedgerClick = (ledgerId: number) => {
  emit("view-ledger", ledgerId);
};

const handleEdit = (ledger: LedgerEntry) => {
  emit("edit-ledger", ledger);
};

const handleDelete = async (ledgerId: number) => {
  const result = await confirm.show({
    title: "确认删除",
    message: "确定要删除这条记账吗？此操作不可恢复。",
    confirmText: "删除",
    cancelText: "取消",
    type: "danger",
  });

  if (result) {
    try {
      await data.removeLedger(ledgerId);
      toast.success("删除成功");
      // 删除后重新加载数据（保持当前筛选条件）
      await data.fetchLedgers(selectedCategory.value || undefined);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  }
};

// 监听分类筛选变化
watch(selectedCategory, async (newValue) => {
  await data.fetchLedgers(newValue || undefined);
});

// 组件挂载时加载数据
onMounted(async () => {
  await data.fetchLedgers();
});
</script>

<style scoped>
.card {
  @apply bg-white p-4 rounded-xl shadow;
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

