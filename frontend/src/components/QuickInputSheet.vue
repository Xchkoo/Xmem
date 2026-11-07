<template>
  <transition name="sheet">
    <div v-if="visible" class="sheet-mask" @click.self="close">
      <section class="sheet">
        <div class="grip" />
        <h3 class="title">快速输入</h3>
        <textarea
          ref="inputRef"
          v-model="text"
          class="sheet-input"
          rows="3"
          placeholder="记一笔支出，或写一条笔记…"
        />
        <p v-if="error" class="error">{{ error }}</p>
        <div class="actions">
          <button class="btn ghost" :disabled="busy || !canSubmit" @click="submit('note')">
            存为笔记
          </button>
          <button class="btn primary" :disabled="busy || !canSubmit" @click="submit('ledger')">
            记为记账
          </button>
        </div>
      </section>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useDataStore } from "../stores/data";

const props = defineProps<{ visible: boolean }>();
const emit = defineEmits<{ (e: "close"): void }>();

const router = useRouter();
const data = useDataStore();

const text = ref("");
const busy = ref(false);
const error = ref("");
const inputRef = ref<HTMLTextAreaElement | null>(null);

const canSubmit = computed(() => text.value.trim().length > 0);

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) return;
    error.value = "";
    await nextTick();
    inputRef.value?.focus();
  },
);

const close = () => {
  if (busy.value) return;
  emit("close");
};

const reset = () => {
  text.value = "";
  error.value = "";
  busy.value = false;
};

const submit = async (target: "ledger" | "note") => {
  const value = text.value.trim();
  if (!value || busy.value) return;

  busy.value = true;
  error.value = "";
  try {
    if (target === "ledger") {
      await data.addLedger(value);
      reset();
      emit("close");
      router.push("/ledgers");
    } else {
      await data.addNoteWithMD(value);
      reset();
      emit("close");
      router.push("/notes");
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err?.message || "提交失败，请重试";
    busy.value = false;
  }
};
</script>

<style scoped>
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 95;
  background: rgb(var(--c-overlay) / 0.4);
  display: flex;
  align-items: flex-end;
}

.sheet {
  width: 100%;
  background: rgb(var(--c-surface));
  border-radius: 20px 20px 0 0;
  padding: 12px 16px calc(20px + var(--sab, 0px));
  box-shadow: var(--shadow-float);
}

.grip {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background: rgb(var(--c-border));
  margin: 0 auto 12px;
}

.title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
  color: rgb(var(--c-text));
}

.sheet-input {
  width: 100%;
  resize: none;
  border: 1px solid rgb(var(--c-border));
  border-radius: 14px;
  padding: 12px 14px;
  background: rgb(var(--c-bg));
  color: rgb(var(--c-text));
  font-size: 15px;
  line-height: 1.5;
  outline: none;
}

.sheet-input:focus {
  border-color: rgb(var(--c-accent) / 0.5);
}

.error {
  margin-top: 8px;
  font-size: 12px;
  color: #ef4444;
}

.actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 14px;
}

.btn {
  padding: 12px;
  border-radius: 14px;
  border: none;
  font-size: 15px;
  font-weight: 600;
}

.btn.ghost {
  background: rgb(var(--c-surface-2));
  color: rgb(var(--c-text));
}

.btn.primary {
  background: linear-gradient(160deg, #4c8dff, #2f6bff);
  color: #fff;
}

.btn:disabled {
  opacity: 0.5;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.18s ease;
}

.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
</style>
