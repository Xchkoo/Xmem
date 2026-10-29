<template>
  <aside
    class="fixed inset-y-0 right-0 w-[92vw] sm:w-[460px] bg-surface border-l border-border shadow-card flex flex-col ai-assistant z-[60]"
    style="padding-top: var(--sat, 0px); padding-bottom: var(--sab, 0px)"
    :class="{ 'ai-soft-loading': loading, 'ai-dragover': isDragOver }"
    @dragenter.prevent="handleDragEnter"
    @dragleave.prevent="handleDragLeave"
    @dragover.prevent="handleDragOver"
    @drop.prevent="handleDrop"
    role="complementary"
    aria-label="AI 助手侧栏"
  >
    <header class="px-4 py-3 border-b border-border flex items-center justify-between brand-header">
      <div class="flex items-center gap-2">
        <div class="brand-chip">
          <span class="brand-x">X</span><span class="brand-ia">ia</span>
        </div>
        <div class="flex flex-col">
          <span class="text-sm font-semibold text-text">xmem intelligence assistant</span>
          <span v-if="contextSummary" class="text-[11px] text-muted">上下文：{{ contextSummary }}</span>
        </div>
      </div>
      <div class="flex items-center gap-2 relative">
        <button class="icon-btn" @click="startNewConversation" title="新对话">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
        </button>
        <button class="icon-btn" @click="toggleHistory" title="历史">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3M12 22a10 10 0 100-20 10 10 0 000 20z"/>
          </svg>
        </button>
        <button class="icon-btn" @click="toggleHistoryMenu" title="更多">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 7a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 7a1.5 1.5 0 110-3 1.5 1.5 0 010 3z"/>
          </svg>
        </button>
        <div v-if="showHistoryMenu" class="dropdown-menu">
          <button class="dropdown-item" @click="clearHistory">清除历史记录</button>
        </div>
        <button class="icon-btn" @click="close" title="关闭">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </header>

    <div v-if="showHistory" class="px-4 py-3 border-b border-border">
      <div v-if="history.length === 0" class="empty-muted">暂无历史记录</div>
      <div v-else class="history-grid">
        <button
          v-for="(item, idx) in history"
          :key="idx"
          class="history-card"
          @click="loadHistory(idx)"
        >
          <div class="history-title">会话 {{ idx + 1 }}</div>
          <div class="history-meta">消息数 {{ item.messages.length }}</div>
          <div class="history-preview">
            {{ item.messages[item.messages.length - 1]?.content || '...' }}
          </div>
        </button>
      </div>
    </div>

    <div v-if="messages.length === 0 && !loading" class="px-4 py-3 border-b border-border">
      <div class="grid grid-cols-2 gap-3">
        <button class="prompt-card" @click="sendWithText('请总结这个笔记的内容')">
          <div class="prompt-title">总结笔记</div>
          <div class="prompt-sub">帮助你提炼重点内容</div>
        </button>
        <button class="prompt-card" @click="sendWithText('请分析记账记录的消费情况')">
          <div class="prompt-title">分析记账消费</div>
          <div class="prompt-sub">快速了解消费结构</div>
        </button>
        <button class="prompt-card" @click="sendWithText('请帮我优化笔记内容的写作风格')">
          <div class="prompt-title">优化写作</div>
          <div class="prompt-sub">让笔记表达更清晰</div>
        </button>
      </div>
    </div>
    <div v-else class="px-4 py-3 border-b border-border">
      <div class="flex gap-2 overflow-auto custom-scrollbar">
        <button class="chip" @click="sendWithText('请总结这个笔记的内容')">总结笔记</button>
        <button class="chip" @click="sendWithText('请分析记账记录的消费情况')">分析记账消费</button>
        <button class="chip" @click="sendWithText('请帮我优化笔记内容的写作风格')">优化写作</button>
      </div>
    </div>

    <main class="flex-1 overflow-auto px-4 py-3 custom-scrollbar">
      <div v-if="messages.length === 0 && newConversationHint" class="new-chat-card">
        <div class="new-chat-title">开启新对话</div>
        <div class="new-chat-desc">拖拽笔记或记账卡片到右侧作为上下文，或直接在下方输入你的问题。</div>
        <div class="mt-3">
          <button class="btn btn-gradient px-4 py-2" @click="focusInput">开始输入</button>
        </div>
      </div>
      <div v-else class="space-y-3">
        <div v-for="(m, i) in messages" :key="i" class="flex items-start gap-3">
          <div
            class="w-7 h-7 rounded-full flex items-center justify-center text-[10px] bubble-avatar"
            :class="m.role === 'user' ? 'bubble-avatar-user' : 'bubble-avatar-ai'"
          >
            {{ m.role === 'user' ? '我' : 'Xia' }}
          </div>
          <div
            class="flex-1 text-sm whitespace-pre-wrap bubble"
            :class="m.role === 'user' ? 'bubble-user' : 'bubble-ai'"
          >{{ m.content }}</div>
        </div>
        <div v-if="loading" class="space-y-2">
          <div class="ai-skeleton-line w-3/4"></div>
          <div class="ai-skeleton-line w-2/3"></div>
          <div class="ai-skeleton-line w-1/2"></div>
        </div>
        <div v-if="error" class="text-xs text-red-500">{{ error }}</div>
      </div>
    </main>

    <footer class="px-4 py-3 border-t border-border">
      <div class="text-xs text-muted mb-2">
        {{ isDesktop ? "支持拖拽笔记或记账卡片到侧栏，自动作为上下文；Shift+Enter 换行，Enter 发送。" : "点击附件选择笔记或记账作为上下文；Shift+Enter 换行，Enter 发送。" }}
      </div>
      <div class="input-area">
        <div class="input-wrap">
          <div
            :ref="setEditorEl"
            class="input input-pill flex-1 min-h-[64px] draft-editor"
            contenteditable="true"
            data-placeholder="请输入问题或消息..."
            @input="handleEditorInput"
            @keydown="handleEditorKeydown"
            @paste="handlePaste"
            @copy="handleCopy"
            @cut="handleCut"
          />
          <button class="attach-btn" title="添加附件" @click="openAttachPicker">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21.44 11.05l-9.9 9.9a5.5 5.5 0 01-7.78-7.78l9.9-9.9a3.5 3.5 0 015 5l-9.2 9.2a1.5 1.5 0 11-2.12-2.12l8.5-8.5" />
            </svg>
          </button>
        </div>
        <button class="btn btn-gradient send-btn" :disabled="loading || !draftText.trim()" @click="send">
          {{ loading ? '生成中...' : '发送' }}
        </button>
      </div>
    </footer>
    <div
      v-if="showAttachPicker"
      class="attach-overlay"
      :class="{ 'attach-overlay-desktop': isDesktop }"
      @click.self="closeAttachPicker"
    >
      <div class="attach-sheet" :class="{ 'attach-sheet-desktop': isDesktop }">
        <div class="attach-header">
          <div class="text-sm font-semibold text-text">选择附件</div>
          <button class="icon-btn" title="关闭" @click="closeAttachPicker">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="attach-tabs">
          <button class="attach-tab" :class="{ 'attach-tab-active': attachPickerTab === 'notes' }" @click="setAttachPickerTab('notes')">📒 笔记</button>
          <button class="attach-tab" :class="{ 'attach-tab-active': attachPickerTab === 'ledgers' }" @click="setAttachPickerTab('ledgers')">📝 记账</button>
        </div>
        <div class="attach-tools">
          <div class="attach-search">
            <input
              :value="attachSearch"
              type="text"
              class="attach-input"
              :placeholder="attachSearchPlaceholder"
              @input="handleAttachSearchInput"
            />
            <button v-if="attachSearch" class="attach-clear" @click="clearAttachSearch">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="attach-filters">
            <CustomSelect
              v-if="attachPickerTab === 'ledgers'"
              :model-value="attachLedgerCategoryFilter"
              :options="ledgerCategorySelectOptions"
              class="attach-select-sm attach-select-category"
              placeholder="全部分类"
              @update:modelValue="updateAttachLedgerCategoryFilter"
            />
            <CustomSelect
              :model-value="attachSort"
              :options="attachSortOptions"
              class="attach-select-sm attach-select-time"
              placeholder="时间排序"
              @update:modelValue="updateAttachSort"
            />
          </div>
        </div>
        <div class="attach-list custom-scrollbar">
          <template v-if="attachPickerTab === 'notes'">
            <div v-if="filteredAttachNotes.length === 0" class="attach-empty">没有匹配的笔记</div>
            <button
              v-for="n in filteredAttachNotes"
              :key="n.id"
              class="attach-card"
              @click="attachNote(n.id)"
            >
              <div class="attach-card-title">笔记 #{{ n.id }}</div>
              <div class="attach-card-desc">{{ (n.body_md || '').slice(0, 80) }}</div>
            </button>
          </template>
          <template v-else>
            <div v-if="filteredAttachLedgers.length === 0" class="attach-empty">没有匹配的记账</div>
            <button
              v-for="l in filteredAttachLedgers"
              :key="l.id"
              class="attach-card"
              @click="attachLedger(l.id)"
            >
              <div class="attach-card-title">记账 #{{ l.id }}</div>
              <div class="attach-card-desc">{{ l.raw_text || '' }}</div>
              <div class="attach-card-meta">
                <span v-if="l.amount !== undefined">金额: {{ l.amount }}</span>
                <span v-if="l.category">分类: {{ l.category }}</span>
              </div>
            </button>
          </template>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { ComponentPublicInstance } from "vue";
import type { LedgerEntry, Note } from "../stores/data";
import CustomSelect from "./CustomSelect.vue";

type ChatMessage = { role: "user" | "assistant" | "system"; content: string };
type HistoryItem = { messages: ChatMessage[]; context: unknown[] };

defineProps<{
  loading: boolean;
  isDragOver: boolean;
  contextSummary: string;
  showHistory: boolean;
  showHistoryMenu: boolean;
  history: HistoryItem[];
  messages: ChatMessage[];
  newConversationHint: boolean;
  isDesktop: boolean;
  draftText: string;
  error: string | null;
  showAttachPicker: boolean;
  attachPickerTab: "notes" | "ledgers";
  attachSearch: string;
  attachLedgerCategoryFilter: string;
  attachSort: "time_desc" | "time_asc";
  filteredAttachNotes: Note[];
  filteredAttachLedgers: LedgerEntry[];
  attachSearchPlaceholder: string;
  ledgerCategorySelectOptions: { label: string; value: string }[];
  attachSortOptions: { label: string; value: string }[];
  setEditorEl: (el: Element | ComponentPublicInstance | null) => void;
  handleDragEnter: (event?: DragEvent) => void;
  handleDragLeave: (event?: DragEvent) => void;
  handleDragOver: (event?: DragEvent) => void;
  handleDrop: (event?: DragEvent) => void;
  startNewConversation: () => void;
  toggleHistory: () => void;
  toggleHistoryMenu: () => void;
  clearHistory: () => void;
  close: () => void;
  loadHistory: (idx: number) => void;
  sendWithText: (text: string) => void;
  focusInput: () => void;
  handleEditorInput: () => void;
  handleEditorKeydown: (event: KeyboardEvent) => void;
  handlePaste: (event: ClipboardEvent) => void;
  handleCopy: (event: ClipboardEvent) => void;
  handleCut: (event: ClipboardEvent) => void;
  openAttachPicker: () => void;
  closeAttachPicker: () => void;
  setAttachPickerTab: (tab: "notes" | "ledgers") => void;
  attachNote: (id: number) => void;
  attachLedger: (id: number) => void;
  send: () => void;
}>();

const emit = defineEmits<{
  (e: "update:attachSearch", value: string): void;
  (e: "update:attachLedgerCategoryFilter", value: string): void;
  (e: "update:attachSort", value: "time_desc" | "time_asc"): void;
}>();

/**
 * 处理附件搜索输入变化。
 */
const handleAttachSearchInput = (event: Event) => {
  emit("update:attachSearch", (event.target as HTMLInputElement).value);
};

/**
 * 清空附件搜索条件。
 */
const clearAttachSearch = () => {
  emit("update:attachSearch", "");
};

/**
 * 更新记账分类筛选条件。
 */
const updateAttachLedgerCategoryFilter = (value: string) => {
  emit("update:attachLedgerCategoryFilter", value);
};

/**
 * 更新附件排序规则。
 */
const updateAttachSort = (value: string) => {
  if (value !== "time_desc" && value !== "time_asc") return;
  emit("update:attachSort", value);
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
  @apply w-full rounded-xl border border-border bg-surface px-4 py-3 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/40 transition-shadow shadow-sm;
}
.input-area {
  @apply flex items-end gap-3;
}
.input-wrap {
  @apply relative flex-1;
}
.input-pill {
  padding-right: 3rem;
}
.attach-btn {
  @apply absolute right-2.5 bottom-2.5 p-2 rounded-lg border border-border bg-surface2 text-text hover:border-accent/60 hover:bg-surface;
}
.send-btn {
  @apply min-w-[76px] px-4 py-2;
}
.draft-editor {
  white-space: pre-wrap;
  word-break: break-word;
}
.draft-editor:empty:before {
  content: attr(data-placeholder);
  color: rgba(120, 120, 120, 0.8);
}
.draft-editor :deep(.draft-token) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 9999px;
  border: 1px solid rgba(90, 170, 255, 0.6);
  background: rgba(90, 170, 255, 0.12);
  color: rgb(var(--c-text));
  font-size: 12px;
  line-height: 1.2;
  margin: 0 4px 2px 0;
  text-decoration: none;
  cursor: pointer;
}
.draft-editor :deep(.draft-token::before) {
  content: "🔗";
  font-size: 12px;
  opacity: 0.75;
}
.draft-editor :deep(.draft-token:hover) {
  border-color: rgba(90, 170, 255, 0.9);
  background: rgba(90, 170, 255, 0.2);
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-accent text-on-accent shadow-float active:scale-95;
}
.btn-gradient {
  background: linear-gradient(135deg, rgba(255,90,180,0.9), rgba(90,170,255,0.9));
  color: white;
  border-radius: 14px;
  box-shadow: 0 6px 20px rgba(255, 90, 180, 0.25);
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70;
}
.link {
  @apply text-text underline decoration-dotted hover:decoration-solid;
}
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
  border: none;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7);
}
.custom-scrollbar::-webkit-scrollbar-button {
  display: none;
}
.empty-muted {
  @apply text-xs text-muted rounded-xl border border-border/60 px-3 py-2;
  background: rgba(255,255,255,0.04);
}
.history-grid {
  @apply grid grid-cols-2 gap-3;
}
.history-card {
  @apply rounded-2xl border px-3 py-2 text-left transition-all duration-150;
  border-color: rgba(255,90,180,0.28);
  background: linear-gradient(135deg, rgba(255,90,180,0.06), rgba(90,170,255,0.06));
}
.history-card:hover {
  border-color: rgba(255,90,180,0.5);
  transform: translateY(-2px);
}
.history-title {
  @apply text-sm font-semibold text-text;
}
.history-meta {
  @apply text-[11px] text-muted;
}
.history-preview {
  @apply text-xs text-muted mt-1 line-clamp-2;
}
.prompt-card {
  @apply rounded-2xl border px-3 py-3 text-left transition-all duration-150;
  border-color: rgba(90,170,255,0.25);
  background: linear-gradient(135deg, rgba(90,170,255,0.08), rgba(255,90,180,0.08));
}
.prompt-card:hover {
  border-color: rgba(90,170,255,0.45);
  transform: translateY(-2px);
}
.prompt-title {
  @apply text-sm font-semibold text-text;
}
.prompt-sub {
  @apply text-xs text-muted mt-1;
}

.ai-skeleton-line {
  @apply h-3 rounded-full bg-surface2;
}
.ai-soft-loading {
  border-color: rgb(255, 90, 180);
  box-shadow: 0 0 12px rgba(255, 90, 180, 0.28);
  animation: ai-soft-pulse 3.2s ease-in-out infinite;
}
.ai-dragover {
  border-color: rgba(90, 170, 255, 0.9);
  box-shadow: 0 0 0 2px rgba(90, 170, 255, 0.2), 0 10px 24px rgba(90, 170, 255, 0.15);
}
.brand-header {
  backdrop-filter: saturate(160%) blur(8px);
}
.brand-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-weight: 800;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, rgba(255,90,180,0.18), rgba(90,170,255,0.18));
  border: 1px solid rgba(255,90,180,0.3);
  color: rgb(var(--c-text));
  padding: 4px 8px;
  border-radius: 12px;
}
.brand-x {
  background: linear-gradient(135deg, #ff5ab4, #5aaaff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.brand-ia {
  color: rgb(var(--c-text));
}
.icon-btn {
  @apply p-2 rounded-lg border border-border hover:border-accent/50;
}
.dropdown-menu {
  @apply absolute right-2 top-10 bg-surface border border-border rounded-xl shadow-card p-2 z-[70];
}
.dropdown-menu-up {
  top: auto;
  bottom: 48px;
}
.dropdown-item {
  @apply text-sm text-text px-3 py-1.5 rounded-md hover:bg-surface2;
}
.attach-overlay {
  @apply fixed inset-0 z-[80] bg-overlay/40;
}
.attach-overlay-desktop {
  @apply flex items-center justify-center p-4;
}
.attach-sheet {
  @apply absolute inset-0 bg-surface flex flex-col;
}
.attach-sheet-desktop {
  @apply relative w-full max-w-2xl max-h-[80vh] rounded-3xl shadow-float border border-border overflow-hidden;
}
.attach-header {
  @apply px-4 py-4 border-b border-border flex items-center justify-between;
}
.attach-tabs {
  @apply px-4 py-2 flex gap-2 border-b border-border bg-surface;
}
.attach-tools {
  @apply px-4 py-3 border-b border-border bg-surface flex flex-col gap-2;
}
.attach-search {
  @apply relative;
}
.attach-input {
  @apply w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/40;
}
.attach-clear {
  @apply absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text;
}
.attach-filters {
  @apply flex flex-wrap gap-2;
}
.attach-select {
  @apply rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent/40;
}
.attach-select-sm :deep(.input) {
  @apply rounded-xl px-3 py-2 text-sm;
}
.attach-select-sm :deep(button) {
  @apply text-sm;
}
.attach-select-sm :deep(button span) {
  @apply whitespace-nowrap;
}
.attach-select-category {
  width: 120px;
}
.attach-select-time {
  width: 140px;
}
.attach-select-sm :deep(svg) {
  width: 16px;
  height: 16px;
}
.attach-select-sm :deep(.custom-scrollbar) {
  max-height: 200px;
}
.attach-tab {
  @apply px-4 py-2 rounded-full text-sm border border-border text-text;
}
.attach-tab-active {
  @apply bg-accent text-on-accent border-accent shadow-float;
}
.attach-list {
  @apply flex-1 overflow-auto px-4 py-4 space-y-3;
}
.attach-card {
  @apply w-full text-left px-4 py-3 rounded-2xl border border-border bg-surface shadow-sm transition-all duration-150;
}
.attach-card:hover {
  border-color: rgba(90,170,255,0.45);
  background: rgba(90,170,255,0.08);
}
.attach-card-title {
  @apply text-sm font-semibold text-text;
}
.attach-card-desc {
  @apply text-xs text-muted mt-1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.attach-card-meta {
  @apply text-[11px] text-muted mt-2 flex gap-3;
}
.attach-empty {
  @apply text-sm text-muted text-center mt-10;
}
.chip {
  @apply px-3 py-1.5 rounded-full text-xs border;
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,90,180,0.28);
  color: rgb(var(--c-text));
}
.chip:hover {
  border-color: rgba(255,90,180,0.45);
}
.new-chat-card {
  @apply rounded-2xl border px-4 py-6 text-center;
  border-color: rgba(255,90,180,0.28);
  background: linear-gradient(135deg, rgba(255,90,180,0.06), rgba(90,170,255,0.06));
}
.new-chat-title {
  @apply text-base font-semibold text-text;
}
.new-chat-desc {
  @apply text-xs text-muted mt-1;
}
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.bubble {
  border-radius: 14px;
  padding: 10px 12px;
}
.bubble-user {
  background: rgb(var(--c-accent) / 0.12);
  border: 1px solid rgba(90,170,255,0.3);
  color: rgb(var(--c-text));
}
.bubble-ai {
  background: linear-gradient(135deg, rgba(255,90,180,0.06), rgba(90,170,255,0.06));
  border: 1px solid rgba(255,90,180,0.28);
  color: rgb(var(--c-text));
}
.bubble-avatar {
  border: 1px solid rgba(255,90,180,0.28);
}
.bubble-avatar-ai {
  background: linear-gradient(135deg, rgba(255,90,180,0.25), rgba(90,170,255,0.25));
  color: white;
}
.bubble-avatar-user {
  background: rgb(var(--c-accent));
  color: rgb(var(--c-on-accent));
}
.input-pill {
  border-radius: 14px;
}
@keyframes ai-soft-pulse {
  0% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 12px rgba(255, 90, 180, 0.28);
  }
  33% {
    border-color: rgb(90, 170, 255);
    box-shadow: 0 0 12px rgba(90, 170, 255, 0.28);
  }
  66% {
    border-color: rgb(120, 255, 150);
    box-shadow: 0 0 12px rgba(120, 255, 150, 0.28);
  }
  100% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 12px rgba(255, 90, 180, 0.28);
  }
}
</style>
