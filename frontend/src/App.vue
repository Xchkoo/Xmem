<template>
  <div class="min-h-screen bg-primary">
    <router-view />

    <LoadingOverlay :visible="ui.routeLoading" />

    <FabMenu
      v-if="user.token && !route.path.includes('/editor')"
      @settings="showSettings = true"
      @notes="router.push('/notes')"
      @home="router.push('/')"
      @ledgers="router.push('/ledgers')"
      @todos="router.push('/todos')"
      @statistics="router.push('/statistics')"
    />

    <Settings v-if="user.token" :visible="showSettings" @close="showSettings = false" />

    <Toast />

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

    <LedgerEditor
      :visible="ledgerEditor.visible"
      :ledger="ledgerEditor.ledger"
      @close="ledgerEditor.close()"
      @saved="ledgerEditor.close()"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import FabMenu from "./components/FabMenu.vue";
import Settings from "./components/Settings.vue";
import Toast from "./components/Toast.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import LedgerEditor from "./components/LedgerEditor.vue";
import LoadingOverlay from "./components/LoadingOverlay.vue";
import { useUserStore } from "./stores/user";
import { useConfirmStore } from "./stores/confirm";
import { usePreferencesStore } from "./stores/preferences";
import { useLedgerEditorStore } from "./stores/ledgerEditor";
import { useUiStore } from "./stores/ui";

const router = useRouter();
const route = useRoute();
const user = useUserStore();
const confirm = useConfirmStore();
const ledgerEditor = useLedgerEditorStore();
const ui = useUiStore();
usePreferencesStore().init();

// 全局 UI 状态
const showSettings = ref(false);

</script>
