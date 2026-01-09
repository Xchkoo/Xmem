<template>
  <transition name="fade">
    <div
      v-if="visible"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="handleClose"
    >
      <div class="bg-white rounded-3xl shadow-float w-full max-w-md">
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 class="text-2xl font-bold text-gray-900">修改密码</h2>
          <button @click="handleClose" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">
            ×
          </button>
        </div>
        <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">原密码</label>
            <input
              v-model="form.oldPassword"
              type="password"
              class="input"
              placeholder="请输入原密码"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">新密码</label>
            <input
              v-model="form.newPassword"
              type="password"
              class="input"
              placeholder="请输入新密码"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">确认新密码</label>
            <input
              v-model="form.confirmPassword"
              type="password"
              class="input"
              :class="{ 'border-red-300': form.confirmPassword && form.newPassword !== form.confirmPassword }"
              placeholder="请再次输入新密码"
              required
            />
            <p v-if="form.confirmPassword && form.newPassword !== form.confirmPassword" class="text-red-500 text-xs mt-1">
              两次输入的密码不一致
            </p>
          </div>
          <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>
          <div class="flex gap-3">
            <button type="button" class="btn ghost flex-1" @click="handleClose">
              取消
            </button>
            <button type="submit" class="btn primary flex-1" :disabled="saving">
              {{ saving ? "修改中..." : "确认修改" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { useUserStore } from "../stores/user";
import { useToastStore } from "../stores/toast";

const props = defineProps<{
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "saved"): void;
}>();

const user = useUserStore();
const toast = useToastStore();
const saving = ref(false);
const error = ref("");
const form = reactive({
  oldPassword: "",
  newPassword: "",
  confirmPassword: "",
});

const resetForm = () => {
  form.oldPassword = "";
  form.newPassword = "";
  form.confirmPassword = "";
  error.value = "";
  saving.value = false;
};

watch(
  () => props.visible,
  (v) => {
    if (v) resetForm();
  }
);

const handleClose = () => {
  emit("close");
};

const handleSubmit = async () => {
  error.value = "";
  if (form.newPassword !== form.confirmPassword) {
    error.value = "两次输入的密码不一致";
    return;
  }

  saving.value = true;
  try {
    await user.changePassword(form.oldPassword, form.newPassword);
    toast.success("密码修改成功");
    emit("saved");
  } catch (err: any) {
    error.value = err.response?.data?.detail || "密码修改失败";
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

.input {
  @apply w-full rounded-xl border border-gray-200 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm;
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-gray-900 text-white shadow-float active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn.ghost {
  @apply bg-white text-gray-700 border border-gray-200 hover:border-gray-300 active:scale-95;
}
.shadow-float {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}
</style>

