<template>
  <div class="min-h-screen bg-primary text-gray-900">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
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
        <div class="text-xl font-bold">记账库</div>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div class="space-y-6">
        <!-- 统计卡片 -->
        <LedgerStatsCard 
          v-if="data.ledgerPagination.total > 0"
          @click="handleStatisticsClick"
        />
        
        <div class="bg-white rounded-3xl shadow-float p-4 md:p-6 lg:p-8 mx-auto">
          <!-- 筛选栏 -->
          <div class="mb-6 flex flex-col sm:flex-row gap-3 items-start sm:items-center">
            <label class="text-sm font-medium text-gray-700 whitespace-nowrap">分类筛选：</label>
            <div class="flex-1 max-w-xs">
              <CustomSelect
                v-model="selectedCategory"
                :options="categoryOptions"
                placeholder="全部"
              />
            </div>
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
        <div v-else-if="!loading" class="text-center py-12">
          <p class="text-gray-400 text-lg">还没有记账</p>
          <p class="text-gray-400 text-sm mt-2">在主界面添加你的第一条记账吧</p>
        </div>
        <div v-else class="text-center py-12">
          <p class="text-gray-400">加载中...</p>
        </div>

        <!-- 分页 -->
        <div v-if="data.ledgerPagination.totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
          <button
            @click="loadPage(currentPage - 1)"
            :disabled="currentPage <= 1"
            class="btn ghost px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <span class="text-sm text-gray-600">
            第 {{ currentPage }} / {{ data.ledgerPagination.totalPages }} 页
            (共 {{ data.ledgerPagination.total }} 条)
          </span>
          <button
            @click="loadPage(currentPage + 1)"
            :disabled="currentPage >= data.ledgerPagination.totalPages"
            class="btn ghost px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
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
import LedgerCardContent from "../components/LedgerCardContent.vue";
import LedgerStatsCard from "../components/LedgerStatsCard.vue";
import CustomSelect from "../components/CustomSelect.vue";
import type { LedgerEntry } from "../stores/data";
import { useRouter } from "vue-router";
import { useLedgerEditorStore } from "../stores/ledgerEditor";

const router = useRouter();

const data = useDataStore();
const confirm = useConfirmStore();
const toast = useToastStore();
const loading = ref(false);
const currentPage = ref(1);
const pageSize = 20;
const selectedCategory = ref("");
const ledgerEditor = useLedgerEditorStore();

// 监听分类变化，自动重新加载
watch(selectedCategory, async () => {
  currentPage.value = 1;
  await loadPage(1);
});

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

// 分类选项
const categoryOptions = [
  { label: "全部", value: "" },
  ...categories.map(cat => ({ label: cat, value: cat }))
];

// 处理分类筛选变化
const handleCategoryChange = async () => {
  currentPage.value = 1; // 重置到第一页
  await loadPage(1);
};

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

const handleLedgerClick = (ledgerId: number) => {
  router.push({ name: "ledger-view", params: { ledgerId } });
};

const handleEdit = (ledger: LedgerEntry) => {
  ledgerEditor.open(ledger);
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
      // 重新加载当前页
      await loadPage(currentPage.value);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  }
};

// 加载指定页
const loadPage = async (page: number) => {
  if (page < 1) return;
  // 如果已经有总页数，检查是否超出范围
  if (data.ledgerPagination.totalPages > 0 && page > data.ledgerPagination.totalPages) return;
  
  loading.value = true;
  try {
    currentPage.value = page;
    const category = selectedCategory.value || undefined;
    const result = await data.fetchLedgers(category, page, pageSize);
    console.log("加载记账数据:", result); // 调试用
  } catch (error: any) {
    console.error("加载记账数据失败:", error); // 调试用
    toast.error(error.response?.data?.detail || "加载失败");
  } finally {
    loading.value = false;
  }
};

// 处理统计点击
const handleStatisticsClick = () => {
  router.push({ name: "statistics" });
};

// 组件挂载时加载第一页
onMounted(async () => {
  await loadPage(1);
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

