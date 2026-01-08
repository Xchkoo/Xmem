<template>
  <!-- 未登录时显示登录注册页面 -->
  <Auth v-if="!user.token" />
  
  <div v-else class="min-h-screen bg-primary">
    <!-- 路由视图：显示当前页面 -->
    <!-- 监听子页面发出的事件以处理全局交互 -->
    <router-view
      @view-notes="router.push('/notes')"
      @view-ledgers="router.push('/ledgers')"
      @view-todos="router.push('/todos')"
      @view-note-detail="(id) => router.push(`/note/${id}`)"
      @edit-note="(id) => router.push(`/editor/${id}`)"
      @view-ledger-detail="(id) => router.push(`/ledger/${id}`)"
      @statistics="router.push('/statistics')"
    ></router-view>

    <!-- 全局组件 -->
    <!-- FabMenu: 悬浮导航菜单 -->
    <FabMenu 
      v-if="!route.path.includes('/editor')"
      @settings="showSettings = true" 
      @notes="router.push('/notes')" 
      @home="router.push('/')"
      @ledgers="router.push('/ledgers')"
      @todos="router.push('/todos')"
      @statistics="router.push('/statistics')"
    />
      
    <!-- 设置弹窗 -->
    <Settings :visible="showSettings" @close="showSettings = false" />
      
    <!-- Toast 提示 -->
    <Toast />
    
    <!-- 确认对话框 -->
    <ConfirmDialog
      :visible="confirm.visible"
      :title="confirm.title"
      :message="confirm.message"
      :confirm-text="confirm.confirmText"
      :cancel-text="confirm.cancelText"
      :type="confirm.type"
      @confirm="confirm.confirm()"
      @cancel="confirm.cancel()"
    />

  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import Auth from "./components/Auth.vue";
import FabMenu from "./components/FabMenu.vue";
import Settings from "./components/Settings.vue";
import Toast from "./components/Toast.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import LedgerEditor from "./components/LedgerEditor.vue";
import { useUserStore } from "./stores/user";
import { useDataStore } from "./stores/data";
import { useConfirmStore } from "./stores/confirm";
import type { LedgerEntry } from "./stores/data";

const router = useRouter();
const route = useRoute();
const user = useUserStore();
const data = useDataStore();
const confirm = useConfirmStore();

// 全局 UI 状态
const showSettings = ref(false);
const showLedgerEditor = ref(false);
const editingLedger = ref<LedgerEntry | null>(null);



// Ledger 编辑相关逻辑 (因为是弹窗，所以保留在 App.vue 作为全局组件)
</script>
