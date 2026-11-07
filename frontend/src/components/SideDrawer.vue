<template>
  <div>
    <!-- 抽屉 -->
    <transition name="drawer">
      <div v-if="visible" class="drawer-mask" @click.self="$emit('close')">
        <aside class="drawer" :style="{ paddingTop: 'calc(20px + var(--sat, 0px))' }">
          <!-- 用户信息 -->
          <div class="profile">
            <div class="avatar">{{ initial }}</div>
            <div class="meta">
              <div class="name">{{ displayName }}</div>
              <div class="email">{{ user.profile?.email || "" }}</div>
            </div>
          </div>

          <!-- 菜单 -->
          <nav class="menu">
            <button class="menu-item" type="button" @click="go('/settings')">
              <span class="menu-icon" v-html="icons.settings" />
              <span>设置</span>
            </button>
            <button class="menu-item" type="button" @click="go('/notes/export')">
              <span class="menu-icon" v-html="icons.export" />
              <span>导出笔记</span>
            </button>
            <button class="menu-item danger" type="button" @click="logout">
              <span class="menu-icon" v-html="icons.logout" />
              <span>退出登录</span>
            </button>
          </nav>

          <div class="footer">Xmem v{{ version }}</div>
        </aside>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../stores/user";
import { APP_VERSION } from "../constants";

const props = defineProps<{ visible: boolean }>();
const emit = defineEmits<{ (e: "close"): void }>();

const router = useRouter();
const user = useUserStore();
const version = APP_VERSION;

const icons = {
  settings:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path stroke-linecap="round" stroke-linejoin="round" d="M4 7h16M4 12h16M4 17h16"/></svg>',
  export:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v11"/><path stroke-linecap="round" stroke-linejoin="round" d="m8 10 4 4 4-4"/><path stroke-linecap="round" stroke-linejoin="round" d="M5 17v3h14v-3"/></svg>',
  logout:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 4H5v16h5"/><path stroke-linecap="round" stroke-linejoin="round" d="M16 8l4 4-4 4"/><path stroke-linecap="round" d="M20 12H9"/></svg>',
};

const displayName = computed(() => {
  return user.profile?.user_name || user.profile?.email?.split("@")[0] || "未命名";
});

const initial = computed(() => (displayName.value || "X").slice(0, 1).toUpperCase());

const go = (path: string) => {
  emit("close");
  router.push(path);
};

const logout = () => {
  emit("close");
  user.logout();
  router.replace({ name: "login" });
};
</script>

<style scoped>
.drawer-mask {
  position: fixed;
  inset: 0;
  z-index: 96;
  background: rgb(var(--c-overlay) / 0.4);
  display: flex;
}

.drawer {
  width: 78vw;
  max-width: 300px;
  height: 100%;
  background: rgb(var(--c-surface));
  border-right: 1px solid rgb(var(--c-border));
  display: flex;
  flex-direction: column;
  padding-left: var(--sal, 0px);
  box-sizing: border-box;
}

.profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 20px 20px;
  border-bottom: 1px solid rgb(var(--c-border));
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(160deg, #4c8dff, #2f6bff);
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.meta {
  min-width: 0;
}

.name {
  font-size: 15px;
  font-weight: 600;
  color: rgb(var(--c-text));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.email {
  font-size: 12px;
  color: rgb(var(--c-text-muted));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu {
  padding: 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: rgb(var(--c-text));
  font-size: 15px;
  text-align: left;
}

.menu-item:active {
  background: rgb(var(--c-surface-2));
}

.menu-item.danger {
  color: #ef4444;
}

.menu-icon {
  width: 20px;
  height: 20px;
  display: flex;
}

.menu-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.footer {
  margin-top: auto;
  padding: 16px 20px calc(16px + var(--sab, 0px));
  font-size: 12px;
  color: rgb(var(--c-text-muted));
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.18s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
</style>
