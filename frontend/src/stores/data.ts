import { defineStore } from "pinia";
import api from "../api/client";

export interface Note {
  id: number;
  body_md: string;
  images?: string[] | null;
  files?: Array<{ name: string; url: string; size: number }> | null;
  attachment_url?: string;
  is_pinned?: boolean;
  created_at: string;
}

export interface LedgerEntry {
  id: number;
  raw_text: string;
  amount?: number;
  category?: string;
  currency: string;
  status: "pending" | "processing" | "completed" | "failed";
  task_id?: string | null;
  merchant?: string | null;
  event_time?: string | null;
  meta?: any;
  created_at: string;
  updated_at?: string | null;
}

export interface Todo {
  id: number;
  title: string;
  completed: boolean;
}

export const useDataStore = defineStore("data", {
  state: () => ({
    notes: [] as Note[],
    ledgers: [] as LedgerEntry[],
    todos: [] as Todo[],
    loading: false
  }),
  actions: {
    async loadAll() {
      await Promise.all([this.fetchNotes(), this.fetchLedgers(), this.fetchTodos()]);
    },
    async fetchNotes(searchQuery?: string) {
      const config = searchQuery && searchQuery.trim() ? { params: { q: searchQuery.trim() } } : {};
      const { data } = await api.get("/notes", config);
      // 确保完全替换 notes 数组，触发响应式更新
      // 后端已经按置顶优先排序，但前端也做一次排序确保正确
      const notes = data || [];
      notes.sort((a, b) => {
        if (a.is_pinned && !b.is_pinned) return -1;
        if (!a.is_pinned && b.is_pinned) return 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      this.notes = notes;
    },
    async fetchLedgers(category?: string) {
      const config = category && category.trim() ? { params: { category: category.trim() } } : {};
      const { data } = await api.get("/ledger", config);
      this.ledgers = data;
    },
    async fetchTodos() {
      const { data } = await api.get("/todos");
      this.todos = data;
    },
    async addNoteWithMD(body_md: string) {
      const { data } = await api.post("/notes", { 
        body_md
      });
      this.notes.unshift(data);
    },
    async uploadImage(file: File): Promise<string> {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/notes/upload-image", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      // 确保URL包含完整的baseURL
      return data.url.startsWith("http") ? data.url : `${api.defaults.baseURL}${data.url}`;
    },
    async uploadFile(file: File): Promise<{ name: string; url: string; size: number }> {
      // 校验文件大小
      if (file.size > 5 * 1024 * 1024) {
        throw new Error(`文件大小不能超过 5MB，当前文件: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
      }
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/notes/upload-file", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      // 确保URL包含完整的baseURL
      const url = data.url.startsWith("http") ? data.url : `${api.defaults.baseURL}${data.url}`;
      return { ...data, url };
    },
    async addLedger(text?: string, imageFile?: File): Promise<LedgerEntry> {
      try {
        let data: LedgerEntry;
        if (imageFile) {
          // 如果有图片，使用 multipart/form-data 提交
          const formData = new FormData();
          if (text) {
            formData.append("text", text);
          }
          formData.append("image", imageFile);
          const response = await api.post("/ledger", formData);
          data = response.data;
        } else if (text) {
          // 只有文本，使用 JSON 提交
          const response = await api.post("/ledger", { text });
          data = response.data;
        } else {
          throw new Error("必须提供文本或图片");
        }
        // 立即添加到列表（pending 状态）
        this.ledgers.unshift(data);
        return data;
      } catch (error: any) {
        console.error("addLedger 失败:", error);
        throw error; // 重新抛出，让调用者处理
      }
    },
    async fetchLedgerStatus(ledgerId: number): Promise<LedgerEntry> {
      const { data } = await api.get(`/ledger/${ledgerId}`);
      // 更新列表中的条目（使用 Vue 的响应式更新方式）
      const index = this.ledgers.findIndex(l => l.id === ledgerId);
      if (index !== -1) {
        // 使用 Object.assign 确保触发响应式更新
        // 或者直接替换整个对象
        this.ledgers[index] = { ...this.ledgers[index], ...data };
      } else {
        // 如果找不到，可能是新创建的，添加到列表
      this.ledgers.unshift(data);
      }
      // 返回更新后的数据
      return this.ledgers[index !== -1 ? index : 0];
    },
    async addTodo(title: string) {
      const { data } = await api.post("/todos", { title });
      this.todos.unshift(data);
    },
    async toggleTodo(id: number) {
      const { data } = await api.patch(`/todos/${id}`);
      this.todos = this.todos.map((t) => (t.id === id ? data : t));
    },
    async removeTodo(id: number) {
      await api.delete(`/todos/${id}`);
      this.todos = this.todos.filter((t) => t.id !== id);
    },
    async removeNote(id: number) {
      try {
      await api.delete(`/notes/${id}`);
      this.notes = this.notes.filter((n) => n.id !== id);
        return true;
      } catch (error) {
        throw error;
      }
    },
    async updateNote(id: number, body_md: string) {
      const { data } = await api.patch(`/notes/${id}`, {
        body_md
      });
      const index = this.notes.findIndex(n => n.id === id);
      if (index !== -1) {
        this.notes[index] = data;
      }
    },
    async togglePinNote(id: number) {
      const { data } = await api.patch(`/notes/${id}/pin`);
      const index = this.notes.findIndex(n => n.id === id);
      if (index !== -1) {
        this.notes[index] = data;
      }
      // 重新排序：置顶的在前
      this.notes.sort((a, b) => {
        if (a.is_pinned && !b.is_pinned) return -1;
        if (!a.is_pinned && b.is_pinned) return 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      return data;
    },
    async updateLedger(id: number, payload: {
      amount?: number;
      currency?: string;
      category?: string;
      merchant?: string;
      raw_text?: string;
      event_time?: string;
    }) {
      const { data } = await api.patch(`/ledger/${id}`, payload);
      const index = this.ledgers.findIndex(l => l.id === id);
      if (index !== -1) {
        this.ledgers[index] = data;
      }
      return data;
    },
    async removeLedger(id: number) {
      try {
        await api.delete(`/ledger/${id}`);
        this.ledgers = this.ledgers.filter((l) => l.id !== id);
        return true;
      } catch (error) {
        throw error;
      }
    }
  }
});

