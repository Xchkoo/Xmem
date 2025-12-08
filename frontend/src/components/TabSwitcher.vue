<template>
  <div class="inline-flex bg-white rounded-full p-1 shadow-float">
    <button
      v-for="tab in tabs"
      :key="tab.value"
      :class="[
        'px-4 py-2 text-sm font-semibold rounded-full transition-all duration-200',
        modelValue === tab.value ? 'bg-gray-900 text-white shadow' : 'text-gray-500 hover:text-gray-800'
      ]"
      @click="$emit('update:modelValue', tab.value)"
    >
      {{ tab.label }}
    </button>
  </div>
  <slot />
</template>

<script setup lang="ts">
defineProps<{
  tabs: { label: string; value: string }[];
  modelValue: string;
}>();
defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();
</script>

