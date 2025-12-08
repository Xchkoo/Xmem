import { defineStore } from "pinia";
import api from "../api/client";

export interface Note {
  id: number;
  body: string;
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
    async fetchNotes() {
      const { data } = await api.get("/notes");
      this.notes = data;
    },
    async fetchLedgers() {
      const { data } = await api.get("/ledger");
      this.ledgers = data;
    },
    async fetchTodos() {
      const { data } = await api.get("/todos");
      this.todos = data;
    },
    async addNote(body: string, attachment_url?: string) {
      const { data } = await api.post("/notes", { body, attachment_url });
      this.notes.unshift(data);
    },
    async addLedger(text: string) {
      const { data } = await api.post("/ledger", { text });
      this.ledgers.unshift(data);
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
    }
  }
});

