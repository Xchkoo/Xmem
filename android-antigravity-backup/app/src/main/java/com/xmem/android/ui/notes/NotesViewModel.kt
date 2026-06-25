package com.xmem.android.ui.notes

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmem.android.data.model.Note
import com.xmem.android.data.repository.NoteRepository
import com.xmem.android.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class NotesViewModel @Inject constructor(private val repository: NoteRepository) : ViewModel() {
    private val _state = MutableStateFlow<UiState<List<Note>>>(UiState.Idle)
    val state: StateFlow<UiState<List<Note>>> = _state

    init {
        fetchNotes()
    }

    fun fetchNotes(query: String? = null) {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                repository.fetchNotes(query)
            }.onSuccess { notes ->
                _state.value = UiState.Success(notes)
            }.onFailure {
                _state.value = UiState.Error(it.message ?: "获取笔记失败", it)
            }
        }
    }

    fun togglePin(id: Long) {
        viewModelScope.launch {
            runCatching {
                repository.togglePin(id)
            }.onSuccess {
                fetchNotes()
            }
        }
    }

    fun deleteNote(id: Long) {
        viewModelScope.launch {
            runCatching {
                repository.deleteNote(id)
            }.onSuccess {
                fetchNotes()
            }
        }
    }

    fun saveNote(id: Long?, content: String) {
        viewModelScope.launch {
            runCatching {
                if (id == null) {
                    repository.createNote(content, null, null, null)
                } else {
                    repository.updateNote(id, content)
                }
            }.onSuccess {
                fetchNotes()
            }
        }
    }
}
