<template>
  <div class="min-h-screen bg-primary flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-3xl shadow-float p-8 md:p-10">
        <div class="text-center mb-8">
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Xmem</h1>
          <p class="text-gray-600">个人记账 + 待办</p>
        </div>

        <!-- 表单 -->
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-gray-700 mb-2">昵称</label>
            <input
              v-model="userName"
              type="text"
              class="input"
              placeholder="请输入昵称（可选）"
              maxlength="64"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
            <input
              v-model="email"
              type="email"
              class="input"
              placeholder="请输入邮箱"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
            <input
              v-model="password"
              type="password"
              class="input"
              placeholder="请输入密码"
              required
            />
          </div>
          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-gray-700 mb-2">确认密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="input"
              :class="{ 'border-red-300': confirmPassword && password !== confirmPassword }"
              placeholder="请再次输入密码"
              required
            />
            <p v-if="confirmPassword && password !== confirmPassword" class="text-red-500 text-xs mt-1">
              两次输入的密码不一致
            </p>
          </div>
          <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>
          <button
            type="submit"
            class="btn primary w-full"
            :disabled="loading"
          >
            {{ loading ? "处理中..." : isLogin ? "登录" : "注册" }}
          </button>
          <div class="text-center">
            <button
              type="button"
              class="text-sm text-gray-500 hover:text-gray-700 underline"
              @click="switchMode"
            >
              {{ isLogin ? "没有账号？前往注册" : "已有账号？前往登录" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useUserStore } from "../stores/user";

const user = useUserStore();
const isLogin = ref(true);
const userName = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const error = ref("");
const loading = ref(false);

const switchMode = () => {
  isLogin.value = !isLogin.value;
  userName.value = "";
  confirmPassword.value = "";
  error.value = "";
};

const handleSubmit = async () => {
  error.value = "";
  
  // 注册时校验密码是否匹配
  if (!isLogin.value) {
    if (password.value !== confirmPassword.value) {
      error.value = "两次输入的密码不一致";
      return;
    }
  }
  
  loading.value = true;
  try {
    if (isLogin.value) {
      await user.login(email.value, password.value);
    } else {
      await user.register(email.value, password.value, userName.value || undefined);
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || (isLogin.value ? "登录失败" : "注册失败");
  } finally {
    loading.value = false;
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
  @apply bg-gray-900 text-white shadow-float active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
}
.shadow-float {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}
</style>

