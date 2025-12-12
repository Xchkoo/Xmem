<template>
  <div>
    <!-- 设置界面 -->
    <transition name="fade">
      <div v-if="visible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="close">
        <div class="bg-white rounded-3xl shadow-float w-full max-w-md max-h-[90vh] overflow-y-auto">
          <!-- 头部 -->
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900">设置</h2>
            <button @click="close" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">
              ×
            </button>
          </div>

          <!-- 内容 -->
          <div class="p-6 space-y-6">
            <!-- 账户信息 -->
            <div>
              <h3 class="text-sm font-semibold text-gray-500 mb-4">账户信息</h3>
              <div class="bg-primary rounded-2xl p-4">
                <div>
                  <label class="block text-sm text-gray-600 mb-1">邮箱</label>
                  <div class="text-gray-900 font-medium">{{ user.profile?.email }}</div>
                </div>
              </div>
            </div>

            <!-- 操作 -->
            <div>
              <h3 class="text-sm font-semibold text-gray-500 mb-4">操作</h3>
              <div class="space-y-2">
                <button class="btn ghost w-full text-left" @click="showChangePassword = true">
                  🔒 修改密码
                </button>
                <button class="btn ghost w-full text-left" @click="handleLogout">
                  🚪 退出登录
                </button>
              </div>
            </div>

            <!-- 偏好设置 -->
            <div>
              <h3 class="text-sm font-semibold text-gray-500 mb-4">偏好设置</h3>
              <div class="bg-primary rounded-2xl p-4 space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="text-sm font-medium text-gray-900">快速笔记下快速删除</div>
                    <div class="text-xs text-gray-500 mt-1">开启后，删除主页面笔记时无需二次确认</div>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      v-model="quickDeleteEnabled"
                      @change="saveQuickDeleteSetting"
                      class="sr-only peer"
                    />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gray-900"></div>
                  </label>
                </div>
              </div>
            </div>

            <!-- 关于 -->
            <div>
              <h3 class="text-sm font-semibold text-gray-500 mb-4">关于</h3>
              <div class="bg-primary rounded-2xl p-4 text-sm text-gray-600">
                <p class="mb-2">Xmem 个人记账 + 待办</p>
                <p class="text-xs text-gray-400 mb-3">版本 1.0.0</p>
                <div>
                  <label class="block text-sm text-gray-600 mb-1">作者</label>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-900 font-medium">Xchkoo</span>
                    <a 
                      href="http://github.com/Xchkoo" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      class="link-github"
                    >
                      🔗 GitHub
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 修改密码弹窗 -->
    <transition name="fade">
      <div v-if="showChangePassword" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="showChangePassword = false">
        <div class="bg-white rounded-3xl shadow-float w-full max-w-md">
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900">修改密码</h2>
            <button @click="showChangePassword = false" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">
              ×
            </button>
          </div>
          <form @submit.prevent="handleChangePassword" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">原密码</label>
              <input
                v-model="passwordForm.oldPassword"
                type="password"
                class="input"
                placeholder="请输入原密码"
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">新密码</label>
              <input
                v-model="passwordForm.newPassword"
                type="password"
                class="input"
                placeholder="请输入新密码"
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">确认新密码</label>
              <input
                v-model="passwordForm.confirmPassword"
                type="password"
                class="input"
                :class="{ 'border-red-300': passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword }"
                placeholder="请再次输入新密码"
                required
              />
              <p v-if="passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword" class="text-red-500 text-xs mt-1">
                两次输入的密码不一致
              </p>
            </div>
            <div v-if="passwordError" class="text-red-500 text-sm">{{ passwordError }}</div>
            <div class="flex gap-3">
              <button type="button" class="btn ghost flex-1" @click="showChangePassword = false">
                取消
              </button>
              <button type="submit" class="btn primary flex-1" :disabled="changingPassword">
                {{ changingPassword ? "修改中..." : "确认修改" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useUserStore } from "../stores/user";

const user = useUserStore();

defineProps<{
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const showChangePassword = ref(false);
const changingPassword = ref(false);
const passwordError = ref("");
const passwordForm = ref({
  oldPassword: "",
  newPassword: "",
  confirmPassword: ""
});

// 快速删除设置
const quickDeleteEnabled = ref(false);

// 从 localStorage 加载快速删除设置
const loadQuickDeleteSetting = () => {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("quickDeleteEnabled");
    quickDeleteEnabled.value = saved === "true";
  }
};

// 保存快速删除设置到 localStorage
const saveQuickDeleteSetting = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem("quickDeleteEnabled", String(quickDeleteEnabled.value));
  }
};

onMounted(() => {
  loadQuickDeleteSetting();
});

const close = () => {
  emit("close");
};

const handleLogout = () => {
  user.logout();
  close();
};

const handleChangePassword = async () => {
  passwordError.value = "";
  
  // 验证密码是否匹配
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordError.value = "两次输入的密码不一致";
    return;
  }
  
  changingPassword.value = true;
  try {
    await user.changePassword(passwordForm.value.oldPassword, passwordForm.value.newPassword);
    showChangePassword.value = false;
    passwordForm.value = { oldPassword: "", newPassword: "", confirmPassword: "" };
    alert("密码修改成功");
  } catch (err: any) {
    passwordError.value = err.response?.data?.detail || "密码修改失败";
  } finally {
    changingPassword.value = false;
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

.shadow-float {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.link-github {
  @apply inline-flex items-center gap-1 text-gray-700 hover:text-gray-900 transition-colors duration-150;
  text-decoration: none;
}

.link-github:hover {
  @apply text-gray-900;
}

.input {
  @apply w-full rounded-xl border border-gray-200 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-shadow shadow-sm;
}
</style>

