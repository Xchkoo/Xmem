package com.xmem.android.ui.ai

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmem.android.data.model.ChatMessage
import com.xmem.android.data.repository.ChatRepository
import com.xmem.android.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AiViewModel @Inject constructor(private val repository: ChatRepository) : ViewModel() {
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages

    private val _state = MutableStateFlow<UiState<Unit>>(UiState.Idle)
    val state: StateFlow<UiState<Unit>> = _state

    fun sendMessage(text: String) {
        val userMsg = ChatMessage(role = "user", content = text)
        _messages.value = _messages.value + userMsg
        _state.value = UiState.Loading
        
        viewModelScope.launch {
            runCatching {
                repository.chat(text, _messages.value.dropLast(1))
            }.onSuccess { response ->
                val assistantMsg = ChatMessage(role = "assistant", content = response.content)
                _messages.value = _messages.value + assistantMsg
                _state.value = UiState.Success(Unit)
            }.onFailure {
                _state.value = UiState.Error(it.message ?: "发送失败", it)
            }
        }
    }

    fun clearChat() {
        _messages.value = emptyList()
    }
}
