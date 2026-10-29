<template>
  <div>
    <!-- 设置界面 -->
    <transition name="fade">
      <div
        v-if="visible && !showChangePassword"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="close"
      >
        <div class="bg-surface rounded-3xl shadow-float w-full max-w-md flex flex-col relative settings-modal">
          <!-- 头部 -->
          <div class="flex items-center justify-between p-6 border-b border-border flex-shrink-0">
            <h2 class="text-2xl font-bold text-text">设置</h2>
            <button @click="close" class="text-muted hover:text-text text-2xl leading-none">
              ×
            </button>
          </div>

          <!-- 内容区域容器 -->
          <div class="relative flex-1 min-h-0">
            <!-- 内容 -->
            <div 
              class="p-6 space-y-6 overflow-y-auto h-full hide-scrollbar scroll-content"
              @scroll="handleScroll"
              ref="scrollContainer"
            >
              <!-- 账户信息 -->
              <div>
                <h3 class="text-sm font-semibold text-muted mb-4">账户信息</h3>
                <div class="bg-primary rounded-2xl p-4 space-y-4">
                  <div>
                    <label class="block text-sm text-muted mb-1">用户名</label>
                    <div class="text-text font-medium">{{ user.profile?.user_name || '未设置' }}</div>
                  </div>
                  <div>
                    <label class="block text-sm text-muted mb-1">邮箱</label>
                    <div class="text-text font-medium">{{ user.profile?.email }}</div>
                  </div>
                </div>
              </div>

              <!-- 操作 -->
              <div>
                <h3 class="text-sm font-semibold text-muted mb-4">操作</h3>
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
                <h3 class="text-sm font-semibold text-muted mb-4">偏好设置</h3>
                <div class="bg-primary rounded-2xl p-4 space-y-4">
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="text-sm font-medium text-text">主页面快速删除笔记</div>
                      <div class="text-xs text-muted mt-1">开启后，删除主页面笔记时无需二次确认</div>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        v-model="quickDeleteEnabled"
                        class="sr-only peer"
                      />
                      <div class="w-11 h-6 bg-surface2 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                    </label>
                  </div>
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="text-sm font-medium text-text">复制笔记为纯文本</div>
                      <div class="text-xs text-muted mt-1">开启后，复制时会移除 Markdown 格式</div>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        v-model="copyPlainEnabled"
                        class="sr-only peer"
                      />
                      <div class="w-11 h-6 bg-surface2 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                    </label>
                  </div>
                  <div v-if="captureSupported" class="flex items-center justify-between">
                    <div>
                      <div class="text-sm font-medium text-text">截图后先预览再上传</div>
                      <div class="text-xs text-muted mt-1">开启后，快捷开关截屏会先发通知预览，确认后才上传</div>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        v-model="capturePreviewEnabled"
                        class="sr-only peer"
                      />
                      <div class="w-11 h-6 bg-surface2 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                    </label>
                  </div>
                </div>
              </div>

              <!-- 外观 -->
              <div>
                <h3 class="text-sm font-semibold text-muted mb-4">外观</h3>
                <div class="bg-primary rounded-2xl p-4 space-y-4">
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="text-sm font-medium text-text">跟随系统主题</div>
                      <div class="text-xs text-muted mt-1">开启后，可切换到“跟随系统”模式并实时响应系统主题变化</div>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        v-model="followSystemEnabled"
                        class="sr-only peer"
                      />
                      <div class="w-11 h-6 bg-surface2 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                    </label>
                  </div>
                </div>
              </div>

              <!-- 关于 -->
              <div>
                <h3 class="text-sm font-semibold text-muted mb-4">关于</h3>
                <div class="bg-primary rounded-2xl p-4 text-sm text-muted">
                  <p class="mb-2">Xmem 个人记账 + 待办</p>
                  <p class="text-xs text-muted mb-3">版本 {{ APP_VERSION }}</p>
                  <div>
                    <label class="block text-sm text-muted mb-1">作者</label>
                    <div class="flex items-center justify-between">
                      <span class="text-text font-medium">Xchkoo</span>
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
                  <div class="mt-4 pt-4 border-t border-border text-xs text-muted space-y-1">
                    <div>备案号：{{ ICP_LICENSE }}</div>
                    <div>版本号：{{ APP_VERSION }}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 底部渐变遮罩 -->
            <div 
              class="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-surface to-transparent pointer-events-none transition-opacity duration-300 rounded-b-3xl"
              :class="{ 'opacity-0': isScrolledToBottom, 'opacity-100': !isScrolledToBottom }"
            ></div>
          </div>
        </div>
      </div>
    </transition>

    <ChangePasswordDialog
      :visible="visible && showChangePassword"
      @close="showChangePassword = false"
      @saved="showChangePassword = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "../stores/user";
import { usePreferencesStore } from "../stores/preferences";
import { useThemeStore } from "../stores/theme";
import { APP_VERSION, ICP_LICENSE } from "../constants";
import { useLedgerEditorStore } from "../stores/ledgerEditor";
import ChangePasswordDialog from "./ChangePasswordDialog.vue";
import { isNativeCaptureAvailable, nativeCapture } from "../utils/nativeCapture";

const user = useUserStore();
const preferences = usePreferencesStore();
const theme = useThemeStore();
const ledgerEditor = useLedgerEditorStore();
const router = useRouter();
const route = useRoute();

const props = defineProps<{
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const showChangePassword = ref(false);

// 截屏记账开关只存在于 Android 原生壳；Web 端整行不渲染
const captureSupported = isNativeCaptureAvailable();
const capturePreviewEnabled = ref(false);
watch(capturePreviewEnabled, (enabled) => {
  void nativeCapture.setPreviewEnabled(enabled);
});

// 滚动相关状态
const scrollContainer = ref<HTMLElement | null>(null);
const isScrolledToBottom = ref(false);

const handleScroll = () => {
  const el = scrollContainer.value;
  if (!el) return;
  
  // 判断是否滚动到底部 (容差 10px)
  isScrolledToBottom.value = Math.abs(el.scrollHeight - el.scrollTop - el.clientHeight) < 10;
};

// 监听 visible 变化，重置滚动状态
watch(() => props.visible, async (newVal) => {
  if (newVal) {
    await nextTick();
    handleScroll(); // 初始化检查一次
    if (captureSupported) {
      const state = await nativeCapture.getState();
      if (state) capturePreviewEnabled.value = state.previewEnabled;
    }
  } else {
    showChangePassword.value = false;
  }
});

const quickDeleteEnabled = computed({
  get: () => preferences.quickDeleteEnabled,
  set: (value) => preferences.setQuickDeleteEnabled(value),
});

const copyPlainEnabled = computed({
  get: () => preferences.noteCopyFormat === "plain",
  set: (value) => preferences.setNoteCopyFormat(value ? "plain" : "raw"),
});

const followSystemEnabled = computed({
  get: () => theme.autoEnabled,
  set: (value) => theme.setAutoEnabled(value),
});

const close = () => {
  emit("close");
};

const handleLogout = async () => {
  close();
  ledgerEditor.close();
  user.logout();
  await router.replace({
    name: "login",
    query: { redirect: route.fullPath },
  });
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
  @apply w-full rounded-xl border border-border bg-surface px-4 py-3 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 transition-shadow shadow-sm;
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-accent text-on-accent shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70 active:scale-95;
}
.shadow-float {
  box-shadow: var(--shadow-float);
}
.link-github {
  @apply text-sm text-muted hover:text-text underline transition-colors;
}

/* 隐藏滚动条 */
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* 响应式高度设置 */
.settings-modal {
  height: 65vh;
}
@media (min-width: 768px) {
  .settings-modal {
    height: 80vh;
  }
}
</style>
