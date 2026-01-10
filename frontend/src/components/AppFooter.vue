<template>
  <footer class="w-full max-w-4xl px-4 py-4">
    <div class="text-center text-xs text-gray-500 space-y-1">
      <div>备案号：{{ ICP_LICENSE }}</div>
      <div>版本号：{{ APP_VERSION }}</div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { APP_VERSION, ICP_LICENSE } from "../constants";
</script>

