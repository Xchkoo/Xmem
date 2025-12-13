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
  is_pinned?: boolean;
  group_id?: number | null;
  group_items?: Todo[];
  created_at: string;
}

export interface LedgerStatistics {
  monthly_data: Array<{ month: string; amount: number; count: number }>;
  yearly_data: Array<{ month: string; amount: number; count: number }>;
  category_stats: Array<{ category: string; amount: number; count: number; percentage: number }>;
  current_month_total: number;
  last_month_total: number;
  month_diff: number;
  month_diff_percent: number;
}

export const useDataStore = defineStore("data", {
  state: () => ({
    notes: [] as Note[],
    ledgers: [] as LedgerEntry[],
    todos: [] as Todo[],
    loading: false,
    ledgerPagination: {
      page: 1,
      pageSize: 20,
      total: 0,
      totalPages: 0
    }
  }),
  actions: {
    async loadAll() {
      await Promise.all([this.fetchNotes(), this.fetchLedgers(undefined, 1, 20), this.fetchTodos(false)]);
    },
    async fetchNotes(searchQuery?: string) {
      const config = searchQuery && searchQuery.trim() ? { params: { q: searchQuery.trim() } } : {};
      const { data } = await api.get("/notes", config);
      // 确保完全替换 notes 数组，触发响应式更新
      // 后端已经按置顶优先排序，但前端也做一次排序确保正确
      const notes: Note[] = data || [];
      notes.sort((a, b) => {
        if (a.is_pinned && !b.is_pinned) return -1;
        if (!a.is_pinned && b.is_pinned) return 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      this.notes = notes;
    },
    async fetchLedgers(category?: string, page: number = 1, pageSize: number = 20) {
      const params: any = { page, page_size: pageSize };
      if (category && category.trim()) {
        params.category = category.trim();
      }
      
      try {
        const token = localStorage.getItem("token");
        console.log("请求参数:", params, "Token:", token ? "存在" : "不存在");
        
        const response = await api.get("/ledger", { params });
        const data = response.data;
        console.log("API 响应数据:", data); // 调试用
        
        // 如果是第一页，替换整个列表；否则追加
        if (page === 1) {
          this.ledgers = data.items || [];
        } else {
          this.ledgers = [...this.ledgers, ...(data.items || [])];
        }
        // 更新分页信息
        this.ledgerPagination = {
          page: data.page || page,
          pageSize: data.page_size || pageSize,
          total: data.total || 0,
          totalPages: data.total_pages || 0
        };
        console.log("更新后的 ledgers:", this.ledgers.length, "条"); // 调试用
        return data; // 返回分页信息
      } catch (error: any) {
        console.error("fetchLedgers 错误:", error);
        console.error("错误详情:", error.response?.data || error.message);
        throw error;
      }
    },
    async fetchLedgerStatistics() {
      const { data } = await api.get("/ledger/statistics");
      return data;
    },
    async fetchTodos(completed?: boolean) {
      const params = completed !== undefined ? { completed } : {};
      const { data } = await api.get("/todos", { params });
      this.todos = data || [];
      this.sortTodos();
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
    async addTodo(title: string, groupId?: number) {
      const { data } = await api.post("/todos", { title, group_id: groupId || null });
      // 如果是组内待办，需要更新对应组的 group_items
      if (groupId) {
        const group = this.todos.find(t => t.id === groupId);
        if (group) {
          if (!group.group_items) group.group_items = [];
          group.group_items.push(data);
        }
      } else {
        this.todos.push(data);
      }
      // 重新排序
      this.sortTodos();
      return data;
    },
    async updateTodo(id: number, updates: { title?: string; completed?: boolean }) {
      const { data } = await api.patch(`/todos/${id}`, updates);
      // 更新待办
      const index = this.todos.findIndex(t => t.id === id);
      if (index !== -1) {
        this.todos[index] = data;
      } else {
        // 可能是组内待办，需要查找
        for (const todo of this.todos) {
          if (todo.group_items) {
            const itemIndex = todo.group_items.findIndex(item => item.id === id);
            if (itemIndex !== -1) {
              todo.group_items[itemIndex] = data;
              // 如果更新了完成状态，可能需要更新组的完成状态
              if (updates.completed !== undefined) {
                todo.completed = data.completed;
              }
              break;
            }
          }
        }
      }
      // 重新排序
      this.sortTodos();
      return data;
    },
    async toggleTodo(id: number) {
      const todo = this.findTodo(id);
      if (!todo) return;
      const { data } = await api.patch(`/todos/${id}/toggle`);
      
      // 更新待办
      if (todo.group_id) {
        // 是组内待办
        const group = this.todos.find(t => t.id === todo.group_id);
        if (group && group.group_items) {
          const itemIndex = group.group_items.findIndex(item => item.id === id);
          if (itemIndex !== -1) {
            group.group_items[itemIndex] = data;
            // 更新组的完成状态（后端已处理，需要重新获取组数据）
            try {
              const groupResponse = await api.get("/todos", { params: { completed: null } });
              const allTodos = groupResponse.data;
              const updatedGroup = allTodos.find((t: Todo) => t.id === group.id);
              if (updatedGroup) {
                const groupIndex = this.todos.findIndex(t => t.id === group.id);
                if (groupIndex !== -1) {
                  this.todos[groupIndex] = updatedGroup;
                }
              }
            } catch (error) {
              console.error("Failed to refresh group:", error);
            }
          }
        }
      } else {
        // 是组标题或单个待办
        const index = this.todos.findIndex(t => t.id === id);
        if (index !== -1) {
          this.todos[index] = data;
          // 如果是组，需要更新 group_items
          if (data.group_items) {
            this.todos[index].group_items = data.group_items;
          }
        }
      }
      // 重新排序
      this.sortTodos();
      return data;
    },
    async removeTodo(id: number) {
      // 先查找待办，确定是组内待办还是组标题/单个待办
      const todo = this.findTodo(id);
      
      // 如果是组内待办，先从前端状态中移除，然后调用 API
      if (todo && todo.group_id) {
        // 是组内待办
        const group = this.todos.find(t => t.id === todo.group_id);
        if (group && group.group_items) {
          group.group_items = group.group_items.filter(item => item.id !== id);
        }
        // 调用 API 删除
        try {
          await api.delete(`/todos/${id}`);
        } catch (error: any) {
          // 如果待办已经被删除（404），忽略错误
          if (error.response?.status !== 404) {
            throw error;
          }
        }
      } else {
        // 是组标题或单个待办
        // 先从前端状态中移除，避免在删除过程中访问已删除的组内待办
        if (todo) {
          if (todo.group_items && todo.group_items.length > 0) {
            // 删除的是组标题，先从前端状态中移除
            this.todos = this.todos.filter((t) => t.id !== id);
          } else {
            // 删除的是单个待办，直接从前端状态中移除
            this.todos = this.todos.filter((t) => t.id !== id);
          }
        }
        
        // 然后调用 API 删除（删除组时，后端会级联删除所有子待办）
        try {
          await api.delete(`/todos/${id}`);
        } catch (error: any) {
          // 如果待办已经被删除（404），忽略错误，但需要刷新列表以确保状态一致
          if (error.response?.status === 404) {
            await this.fetchTodos();
          } else {
            throw error;
          }
        }
      }
    },
    findTodo(id: number): Todo | null {
      // 查找待办（包括组内待办）
      for (const todo of this.todos) {
        if (todo.id === id) return todo;
        if (todo.group_items) {
          const item = todo.group_items.find(item => item.id === id);
          if (item) return item;
        }
      }
      return null;
    },
    async togglePinTodo(id: number) {
      const { data } = await api.patch(`/todos/${id}/pin`);
      const index = this.todos.findIndex(t => t.id === id);
      if (index !== -1) {
        this.todos[index] = data;
      }
      // 重新排序：置顶的在前
      this.sortTodos();
      return data;
    },
    sortTodos() {
      // 按置顶优先，然后按创建时间倒序排序（最新的在上面）- 只对组标题和单个待办排序
      this.todos.sort((a, b) => {
        // 置顶的在前
        if (a.is_pinned && !b.is_pinned) return -1;
        if (!a.is_pinned && b.is_pinned) return 1;
        // 然后按创建时间倒序
        const timeA = new Date(a.created_at).getTime();
        const timeB = new Date(b.created_at).getTime();
        return timeB - timeA;
      });
      // 组内待办按创建时间正序排序（最新的在下面）
      this.todos.forEach(todo => {
        if (todo.group_items) {
          todo.group_items.sort((a, b) => {
            const timeA = new Date(a.created_at).getTime();
            const timeB = new Date(b.created_at).getTime();
            return timeA - timeB; // 正序：旧的在上，新的在下
          });
        }
      });
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
