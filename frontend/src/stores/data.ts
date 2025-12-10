import { defineStore } from "pinia";
import api from "../api/client";

export interface Note {
  id: number;
  body_md: string;
  images?: string[] | null;
  files?: Array<{ name: string; url: string; size: number }> | null;
  attachment_url?: string;
  created_at: string;
}

export interface LedgerEntry {
  id: number;
  raw_text: string;
  amount?: number;
  category?: string;
  currency: string;
  created_at: string;
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
      this.notes = data || [];
    },
    async fetchLedgers() {
      const { data } = await api.get("/ledger");
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
    async addLedger(text?: string, imageFile?: File) {
      if (imageFile) {
        // 如果有图片，使用 multipart/form-data 提交
        const formData = new FormData();
        if (text) {
          formData.append("text", text);
        }
        formData.append("image", imageFile);
        const { data } = await api.post("/ledger", formData, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        this.ledgers.unshift(data);
      } else if (text) {
        // 只有文本，使用 JSON 提交
        const { data } = await api.post("/ledger", { text });
        this.ledgers.unshift(data);
      } else {
        throw new Error("必须提供文本或图片");
      }
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
    }
  }
});

