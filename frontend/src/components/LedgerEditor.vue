<template>
  <div>
    <!-- 编辑弹窗 -->
    <transition name="fade">
      <div 
        v-if="visible" 
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4" 
        @click.self="handleCancel"
      >
        <div class="bg-white rounded-3xl shadow-float w-full max-w-md max-h-[90vh] overflow-y-auto">
          <!-- 头部 -->
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900">编辑记账</h2>
            <button @click="handleCancel" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">
              ×
            </button>
          </div>

          <!-- 内容 -->
          <div class="p-6 space-y-4">
            <!-- 金额 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">金额</label>
              <input
                v-model.number="form.amount"
                type="number"
                step="0.01"
                class="input"
                placeholder="请输入金额"
              />
            </div>

            <!-- 货币 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">货币</label>
              <CustomSelect
                v-model="form.currency"
                :options="currencyOptions"
                placeholder="请选择货币"
              >
                <template #icon>
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </template>
              </CustomSelect>
            </div>

            <!-- 分类 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">分类</label>
              <CustomSelect
                v-model="form.category"
                :options="categoryOptions"
                placeholder="请选择分类"
              />
            </div>

            <!-- 商家 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">商家</label>
              <input
                v-model="form.merchant"
                type="text"
                class="input"
                placeholder="请输入商家"
              />
            </div>

            <!-- 原始文本 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">原始文本</label>
              <textarea
                v-model="form.raw_text"
                class="input h-24"
                placeholder="请输入原始文本"
              />
            </div>

            <!-- 时间 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">时间</label>
              <input
                v-model="form.event_time"
                type="datetime-local"
                class="input"
              />
            </div>

            <!-- 按钮 -->
            <div class="flex gap-3 pt-4">
              <button type="button" class="btn ghost flex-1" @click="handleCancel">
                取消
              </button>
              <button type="button" class="btn primary flex-1" @click="handleSave" :disabled="saving">
                {{ saving ? "保存中..." : "保存" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";
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

// 转换为选项格式
const categoryOptions = computed(() => 
  categories.map(cat => ({ value: cat, label: cat }))
);

// 货币选项
const currencyOptions = [
  { value: "CNY", label: "CNY (人民币)" },
  { value: "USD", label: "USD (美元)" },
  { value: "EUR", label: "EUR (欧元)" },
  { value: "JPY", label: "JPY (日元)" }
];

const props = defineProps<{
  visible: boolean;
  ledger: LedgerEntry | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "saved"): void;
}>();

const data = useDataStore();
const toast = useToastStore();

const saving = ref(false);
const form = ref({
  amount: undefined as number | undefined,
  currency: "CNY",
  category: "",
  merchant: "",
  raw_text: "",
  event_time: ""
});

// 当 ledger 变化时，更新表单
watch(() => props.ledger, (ledger) => {
  if (ledger) {
    form.value = {
      amount: ledger.amount,
      currency: ledger.currency || "CNY",
      category: ledger.category || "",
      merchant: ledger.merchant || "",
      raw_text: ledger.raw_text || "",
      event_time: ledger.event_time 
        ? new Date(ledger.event_time).toISOString().slice(0, 16)
        : new Date(ledger.created_at).toISOString().slice(0, 16)
    };
  }
}, { immediate: true });

const handleCancel = () => {
  emit("close");
};

const handleSave = async () => {
  if (!props.ledger) return;
  
  saving.value = true;
  try {
    const payload: any = {};
    if (form.value.amount !== undefined) payload.amount = form.value.amount;
    if (form.value.currency) payload.currency = form.value.currency;
    if (form.value.category !== undefined) payload.category = form.value.category;
    if (form.value.merchant !== undefined) payload.merchant = form.value.merchant;
    if (form.value.raw_text !== undefined) payload.raw_text = form.value.raw_text;
    if (form.value.event_time) {
      payload.event_time = new Date(form.value.event_time).toISOString();
    }
    
    await data.updateLedger(props.ledger.id, payload);
    toast.success("保存成功");
    emit("saved");
    emit("close");
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "保存失败");
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}

.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300;
}

.btn.primary {
  @apply bg-gray-900 text-white hover:bg-gray-800;
}

.shadow-float {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.input {
  @apply w-full rounded-xl border border-gray-200 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm;
}
</style>

