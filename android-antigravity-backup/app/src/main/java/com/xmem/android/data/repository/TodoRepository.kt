package com.xmem.android.data.repository

import com.xmem.android.data.model.Todo
import com.xmem.android.data.model.TodoCreateRequest
import com.xmem.android.data.model.TodoUpdateRequest
import com.xmem.android.data.network.ApiService

class TodoRepository(private val api: ApiService) {
    suspend fun fetchTodos(completed: Boolean?): List<Todo> = api.fetchTodos(completed)

    suspend fun createTodo(title: String, groupId: Long?): Todo {
        return api.createTodo(TodoCreateRequest(title = title, group_id = groupId))
    }

    suspend fun updateTodo(id: Long, title: String?, completed: Boolean?): Todo {
        return api.updateTodo(id, TodoUpdateRequest(title = title, completed = completed))
    }

    suspend fun toggleTodo(id: Long): Todo = api.toggleTodo(id)

    suspend fun togglePin(id: Long): Todo = api.toggleTodoPin(id)

    suspend fun deleteTodo(id: Long) {
        api.deleteTodo(id)
    }
}
