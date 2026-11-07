<template>
  <Settings :visible="true" mode="page" @close="handleClose" />
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import Settings from "../components/Settings.vue";

/**
 * /settings 页面（安卓底栏的「设置」）。
 * 复用 Settings 组件，只是换成整屏的 page 模式，而不是桌面端的弹层。
 */
const router = useRouter();

const handleClose = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.push("/notes");
};
</script>
