<template>
  <div class="min-h-screen bg-bg text-text overflow-x-hidden">
    <header class="w-full max-w-5xl mx-auto px-4 pt-8 pb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex min-w-0 items-center gap-4">
        <button
          @click="handleBack"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          <span class="max-[450px]:hidden">返回</span>
        </button>
        <div class="min-w-0 text-xl font-bold">笔记导出</div>
      </div>
    </header>

    <main class="w-full max-w-5xl mx-auto px-4 pb-20 space-y-6">
      <div class="overflow-hidden bg-surface border border-border rounded-3xl shadow-card p-4 sm:p-6 md:p-8 space-y-6">
        <div class="grid gap-6 lg:grid-cols-[1.2fr,1fr]">
          <div class="min-w-0 space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="text-sm font-semibold">选择笔记</div>
              <label class="flex items-center gap-2 text-xs text-muted cursor-pointer">
                <input type="checkbox" class="cursor-pointer" :checked="isAllSelected" @change="toggleSelectAll" />
                全选
              </label>
            </div>
            <div class="max-h-[360px] overflow-y-auto overflow-x-hidden border border-border rounded-2xl divide-y divide-border">
              <label
                v-for="note in data.notes"
                :key="note.id"
                class="flex flex-col gap-2 px-4 py-3 cursor-pointer hover:bg-surface2 transition-colors sm:flex-row sm:items-start sm:justify-between sm:gap-3"
              >
                <div class="flex min-w-0 flex-1 items-center gap-3">
                  <input type="checkbox" class="cursor-pointer" :value="note.id" v-model="selectedNoteIds" />
                  <div class="min-w-0 flex-1">
                    <div class="text-sm font-medium truncate">{{ getNoteTitle(note.body_md) }}</div>
                    <div class="text-xs text-muted truncate">{{ formatTime(note.created_at) }}</div>
                  </div>
                </div>
                <div class="pl-7 text-xs text-muted sm:shrink-0 sm:whitespace-nowrap sm:pl-2">{{ note.body_md?.length || 0 }}字</div>
              </label>
            </div>
          </div>

          <div class="min-w-0 space-y-4">
            <div class="text-sm font-semibold">导出格式</div>
            <div class="text-xs text-muted">CSV 仅导出文本内容，7z 可包含图片与附件</div>
            <div class="grid gap-4">
              <div class="min-w-0 border border-border rounded-2xl p-4 bg-surface2 space-y-3">
                <div class="flex flex-col items-start gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
                  <div class="min-w-0 flex items-center gap-2 text-sm font-semibold">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-400/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    CSV 单文件
                  </div>
                  <button class="btn primary w-full text-xs px-3 py-2 sm:w-auto sm:py-1" @click="startExport('csv')" :disabled="!selectedNoteIds.length">
                    导出
                  </button>
                </div>
                <div class="text-xs text-muted">预计大小：{{ formatBytes(estimatedCsvSize) }}</div>
                <div class="h-2 rounded-full bg-surface overflow-hidden">
                  <div class="h-full bg-blue-400/70 transition-all" :style="{ width: `${csvProgressValue}%` }"></div>
                </div>
                <div class="text-xs text-muted">{{ csvStatusText }}</div>
              </div>

              <div class="min-w-0 border border-border rounded-2xl p-4 bg-surface2 space-y-3">
                <div class="flex flex-col items-start gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
                  <div class="min-w-0 flex items-center gap-2 text-sm font-semibold">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-400/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3l1.8 4.8L19 9l-4.2 2.7L16 16l-4-2.6L8 16l1.2-4.3L5 9l5.2-1.2L12 3z" />
                    </svg>
                    Markdown 7z
                  </div>
                  <button class="btn primary w-full text-xs px-3 py-2 sm:w-auto sm:py-1" @click="startExport('md7z')" :disabled="!selectedNoteIds.length">
                    导出
                  </button>
                </div>
                <div class="text-xs text-muted">预计大小：{{ formatBytes(estimatedMd7zSize) }}</div>
                <div class="h-2 rounded-full bg-surface overflow-hidden">
                  <div class="h-full bg-emerald-400/70 transition-all" :style="{ width: `${md7zProgressValue}%` }"></div>
                </div>
                <div class="text-xs text-muted">{{ md7zStatusText }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8 space-y-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="text-sm font-semibold">导出历史</div>
          <div class="flex flex-wrap items-center gap-2">
            <button class="btn ghost text-xs px-3 py-1" @click="clearExportHistory">清空</button>
            <button class="btn ghost text-xs px-3 py-1" @click="fetchJobs">刷新</button>
          </div>
        </div>
        <div v-if="!jobs.length" class="text-sm text-muted">暂无导出记录</div>
        <div v-else class="space-y-3">
          <div
            v-for="job in jobs"
            :key="job.id"
            class="border border-border rounded-2xl p-4 bg-surface2 space-y-2"
          >
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex min-w-0 items-center gap-2">
                <span class="text-sm font-semibold">{{ job.export_type === 'csv' ? 'CSV 导出' : 'Markdown 7z' }}</span>
                <span class="text-xs text-muted">#{{ job.id }}</span>
              </div>
              <div class="text-xs text-muted">{{ formatTime(job.created_at) }}</div>
            </div>
            <div class="flex flex-wrap items-center gap-3 text-xs text-muted">
              <span>状态：{{ formatExportStatus(job.status) }}</span>
              <span v-if="job.file_size">大小：{{ formatBytes(job.file_size) }}</span>
              <span v-if="job.checksum_sha256" class="break-all">校验：{{ job.checksum_sha256.slice(0, 10) }}...</span>
            </div>
            <div v-if="job.status === 'expired'" class="text-xs text-amber-400">
              文件已过期，请重新导出
            </div>
            <div class="h-2 rounded-full bg-surface overflow-hidden">
              <div class="h-full bg-accent/70 transition-all" :style="{ width: `${job.status === 'completed' ? 100 : job.progress}%` }"></div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <button
                class="btn ghost text-xs px-3 py-1"
                :disabled="job.status !== 'completed'"
                @click="enqueueDownload(job)"
              >
                下载
              </button>
              <button
                class="btn ghost text-xs px-3 py-1"
                :disabled="job.status !== 'completed'"
                @click="downloadChecksum(job)"
              >
                校验报告
              </button>
              <button
                v-if="job.status === 'failed'"
                class="btn ghost text-xs px-3 py-1 text-red-400"
                @click="retryExport(job)"
              >
                重试导出
              </button>
              <span v-if="job.error_message" class="break-all text-xs text-red-400">错误：{{ job.error_message }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8 space-y-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="text-sm font-semibold">下载管理</div>
          <div class="flex flex-wrap items-center gap-2 text-xs text-muted">
            <span>并发数：{{ maxConcurrent }}</span>
            <button class="btn ghost text-xs px-3 py-1" @click="clearDownloadHistory">清空</button>
          </div>
        </div>
        <div v-if="!downloads.length" class="text-sm text-muted">暂无下载任务</div>
        <div v-else class="space-y-3">
          <div v-for="task in downloads" :key="task.id" class="border border-border rounded-2xl p-4 bg-surface2 space-y-2">
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div class="min-w-0 break-all text-sm font-semibold">{{ task.fileName }}</div>
              <div class="text-xs text-muted">{{ task.status }}</div>
            </div>
            <div class="h-2 rounded-full bg-surface overflow-hidden">
              <div class="h-full bg-blue-400/70 transition-all" :style="{ width: `${task.progress}%` }"></div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-xs text-muted">{{ formatBytes(task.downloaded) }} / {{ formatBytes(task.total || 0) }}</span>
              <button v-if="task.status === 'failed'" class="btn ghost text-xs px-3 py-1" @click="retryDownload(task)">重试</button>
              <span v-if="task.error" class="break-all text-xs text-red-400">错误：{{ task.error }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useDataStore } from "../stores/data";
import api from "../api/client";
import { useToastStore } from "../stores/toast";

type ExportJob = {
  id: number;
  export_type: "csv" | "md7z";
  status: "pending" | "processing" | "completed" | "failed" | "expired";
  note_ids?: number[] | null;
  file_name?: string | null;
  file_size?: number | null;
  checksum_sha256?: string | null;
  progress: number;
  error_message?: string | null;
  created_at: string;
};

type DownloadTask = {
  id: string;
  jobId: number;
  fileName: string;
  status: "queued" | "downloading" | "completed" | "failed";
  progress: number;
  downloaded: number;
  total: number | null;
  error?: string;
  parts: Uint8Array[];
};

const router = useRouter();
const data = useDataStore();
const toast = useToastStore();
const handleBack = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.push({ name: "notes" });
};

const selectedNoteIds = ref<number[]>([]);
const jobs = ref<ExportJob[]>([]);
const estimatedCsvSize = ref(0);
const estimatedMd7zSize = ref(0);
const pollingTimer = ref<number | null>(null);

const downloads = ref<DownloadTask[]>([]);
const maxConcurrent = 2;

const isAllSelected = computed(() => data.notes.length > 0 && selectedNoteIds.value.length === data.notes.length);

const latestCsvJob = computed(() => jobs.value.find(job => job.export_type === "csv"));
const latestMd7zJob = computed(() => jobs.value.find(job => job.export_type === "md7z"));

const csvProgress = computed(() => latestCsvJob.value?.progress ?? 0);
const md7zProgress = computed(() => latestMd7zJob.value?.progress ?? 0);
const csvProgressValue = computed(() => (latestCsvJob.value?.status === "completed" ? 100 : csvProgress.value));
const md7zProgressValue = computed(() => (latestMd7zJob.value?.status === "completed" ? 100 : md7zProgress.value));

/** 格式化导出状态文本 */
const formatExportStatus = (status: ExportJob["status"]) => {
  const mapping: Record<ExportJob["status"], string> = {
    pending: "排队中",
    processing: "处理中",
    completed: "已完成",
    failed: "失败",
    expired: "已过期",
  };
  return mapping[status] ?? status;
};

const csvStatusText = computed(() => latestCsvJob.value ? `状态：${formatExportStatus(latestCsvJob.value.status)}` : "尚未开始导出");
const md7zStatusText = computed(() => latestMd7zJob.value ? `状态：${formatExportStatus(latestMd7zJob.value.status)}` : "尚未开始导出");

/** 格式化时间显示 */
const formatTime = (value: string) => {
  const date = new Date(value);
  return date.toLocaleString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

/** 提取笔记标题 */
const getNoteTitle = (markdown?: string | null) => {
  const content = markdown || "";
  const lines = content.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    return trimmed.replace(/^#+\s*/, "").slice(0, 30);
  }
  return "未命名";
};

/** 格式化字节数显示 */
const formatBytes = (value: number) => {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let idx = 0;
  while (size >= 1024 && idx < units.length - 1) {
    size /= 1024;
    idx += 1;
  }
  return `${size.toFixed(size < 10 ? 1 : 0)} ${units[idx]}`;
};

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedNoteIds.value = [];
  } else {
    selectedNoteIds.value = data.notes.map(note => note.id);
  }
};

const fetchJobs = async () => {
  const { data: res } = await api.get("/notes/exports");
  jobs.value = res || [];
};

const refreshEstimates = async () => {
  if (!selectedNoteIds.value.length) {
    estimatedCsvSize.value = 0;
    estimatedMd7zSize.value = 0;
    return;
  }
  const payload = { note_ids: selectedNoteIds.value, include_all: false };
  const [csvRes, mdRes] = await Promise.all([
    api.post("/notes/exports/estimate", { ...payload, export_type: "csv" }),
    api.post("/notes/exports/estimate", { ...payload, export_type: "md7z" }),
  ]);
  estimatedCsvSize.value = csvRes.data?.estimated_size || 0;
  estimatedMd7zSize.value = mdRes.data?.estimated_size || 0;
};

const startExport = async (type: "csv" | "md7z") => {
  if (!selectedNoteIds.value.length) return;
  try {
    await api.post("/notes/exports", {
      export_type: type,
      note_ids: selectedNoteIds.value,
      include_all: false,
    });
    toast.success("导出任务已开始");
    await fetchJobs();
  } catch (error: any) {
    toast.error(error?.response?.data?.detail || "导出失败，请重试");
  }
};

const retryExport = async (job: ExportJob) => {
  try {
    await api.post("/notes/exports", {
      export_type: job.export_type,
      note_ids: job.note_ids || [],
      include_all: false,
    });
    toast.success("已重新提交导出任务");
    await fetchJobs();
  } catch (error: any) {
    toast.error(error?.response?.data?.detail || "重试失败，请稍后再试");
  }
};

const buildDownloadUrl = (jobId: number, type: "download" | "checksum-report") => {
  const base = api.defaults.baseURL || "/api";
  const path = `/notes/exports/${jobId}/${type}`;
  if (base.startsWith("http")) {
    return `${base}${path}`;
  }
  return `${window.location.origin}${base}${path}`;
};

const downloadChecksum = async (job: ExportJob) => {
  try {
    const response = await api.get(`/notes/exports/${job.id}/checksum-report`, { responseType: "blob" });
    const blobUrl = URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = `${job.file_name || "export"}.sha256`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(blobUrl);
  } catch (error: any) {
    toast.error(error?.response?.data?.detail || "下载校验报告失败");
  }
};

const stopPolling = () => {
  if (pollingTimer.value !== null) {
    clearInterval(pollingTimer.value);
    pollingTimer.value = null;
  }
};

const clearExportHistory = async () => {
  try {
    await api.delete("/notes/exports");
    jobs.value = [];
    stopPolling();
    toast.success("导出历史已清空");
  } catch (error: any) {
    toast.error(error?.response?.data?.detail || "清空失败，请重试");
  }
};

const enqueueDownload = (job: ExportJob) => {
  if (!job.file_name) {
    toast.error("文件未生成");
    return;
  }
  if (downloads.value.find(task => task.jobId === job.id)) {
    return;
  }
  downloads.value.push({
    id: `${job.id}-${Date.now()}`,
    jobId: job.id,
    fileName: job.file_name,
    status: "queued",
    progress: 0,
    downloaded: 0,
    total: job.file_size || null,
    parts: [],
  });
  processQueue();
};

const processQueue = () => {
  const active = downloads.value.filter(task => task.status === "downloading").length;
  const available = Math.max(0, maxConcurrent - active);
  if (available <= 0) return;
  const queued = downloads.value.filter(task => task.status === "queued").slice(0, available);
  queued.forEach(task => startDownload(task));
};

const startDownload = async (task: DownloadTask) => {
  task.status = "downloading";
  task.error = undefined;
  try {
    await downloadWithResume(task);
    task.status = "completed";
    task.progress = 100;
  } catch (error: any) {
    task.status = "failed";
    task.error = error?.message || "下载失败";
  } finally {
    processQueue();
  }
};

const retryDownload = (task: DownloadTask) => {
  task.status = "queued";
  task.error = undefined;
  processQueue();
};

const clearDownloadHistory = () => {
  downloads.value = [];
};

const downloadWithResume = async (task: DownloadTask) => {
  const token = localStorage.getItem("token") || "";
  const url = buildDownloadUrl(task.jobId, "download");
  const chunkSize = 2 * 1024 * 1024;
  let start = task.downloaded;
  let total = task.total || 0;
  let retries = 0;

  while (true) {
    const end = start + chunkSize - 1;
    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        Range: `bytes=${start}-${end}`,
      },
    });
    if (!res.ok && res.status !== 206 && res.status !== 200) {
      retries += 1;
      if (retries >= 3) {
        throw new Error("下载失败，请重试");
      }
      continue;
    }
    retries = 0;
    const contentRange = res.headers.get("content-range");
    if (contentRange) {
      const totalMatch = contentRange.match(/\/(\d+)$/);
      if (totalMatch) {
        total = Number(totalMatch[1]);
        task.total = total;
      }
    } else if (!total) {
      const len = res.headers.get("content-length");
      total = len ? Number(len) : total;
      task.total = total || task.total;
    }
    const buffer = await res.arrayBuffer();
    const chunk = new Uint8Array(buffer);
    task.parts.push(chunk);
    start += chunk.byteLength;
    task.downloaded = start;
    task.progress = total ? Math.round((start / total) * 100) : 0;
    if (total && start >= total) break;
    if (!total && res.status === 200) break;
  }

  const blob = new Blob(task.parts);
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = task.fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(blobUrl);
};

watch(selectedNoteIds, () => {
  refreshEstimates();
});

const pollJobs = async () => {
  await fetchJobs();
  const hasRunning = jobs.value.some(job => job.status === "processing" || job.status === "pending");
  if (hasRunning && pollingTimer.value === null) {
    pollingTimer.value = window.setInterval(fetchJobs, 1500);
  }
  if (!hasRunning && pollingTimer.value !== null) {
    stopPolling();
  }
};

onMounted(async () => {
  if (!data.notes.length) {
    await data.fetchNotes();
  }
  selectedNoteIds.value = data.notes.map(note => note.id);
  await refreshEstimates();
  await pollJobs();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-accent text-on-accent shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70;
}
</style>
