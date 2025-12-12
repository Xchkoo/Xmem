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
              <select v-model="form.currency" class="input">
                <option value="CNY">CNY (人民币)</option>
                <option value="USD">USD (美元)</option>
                <option value="EUR">EUR (欧元)</option>
                <option value="JPY">JPY (日元)</option>
              </select>
            </div>

            <!-- 分类 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">分类</label>
              <input
                v-model="form.category"
                type="text"
                class="input"
                placeholder="请输入分类"
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
import { ref, watch } from "vue";
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";
import type { LedgerEntry } from "../stores/data";

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

