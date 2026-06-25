package com.xmem.android.ui.todos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmem.android.data.model.Todo
import com.xmem.android.data.repository.TodoRepository
import com.xmem.android.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TodosViewModel @Inject constructor(private val repository: TodoRepository) : ViewModel() {
    private val _state = MutableStateFlow<UiState<List<Todo>>>(UiState.Idle)
    val state: StateFlow<UiState<List<Todo>>> = _state

    init {
        fetchTodos()
    }

    fun fetchTodos(completed: Boolean? = null) {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                repository.fetchTodos(completed)
            }.onSuccess { todos ->
                _state.value = UiState.Success(todos)
            }.onFailure {
                _state.value = UiState.Error(it.message ?: "获取待办失败", it)
            }
        }
    }

    fun toggleTodo(id: Long) {
        viewModelScope.launch {
            runCatching {
                repository.toggleTodo(id)
            }.onSuccess {
                fetchTodos()
            }
        }
    }

    fun addTodo(title: String, groupId: Long? = null) {
        viewModelScope.launch {
            runCatching {
                repository.createTodo(title, groupId)
            }.onSuccess {
                fetchTodos()
            }
        }
    }

    fun deleteTodo(id: Long) {
        viewModelScope.launch {
            runCatching {
                repository.deleteTodo(id)
            }.onSuccess {
                fetchTodos()
            }
        }
    }
}
