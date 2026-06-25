package com.xmem.android.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmem.android.data.repository.AuthRepository
import com.xmem.android.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(private val repository: AuthRepository) : ViewModel() {
    private val _state = MutableStateFlow<UiState<Unit>>(UiState.Idle)
    val state: StateFlow<UiState<Unit>> = _state

    fun login(email: String, password: String) {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                repository.login(email, password)
            }.onSuccess {
                _state.value = UiState.Success(Unit)
            }.onFailure {
                _state.value = UiState.Error(it.message ?: "登录失败", it)
            }
        }
    }

    fun register(email: String, password: String, userName: String?) {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                repository.register(email, password, userName)
            }.onSuccess {
                _state.value = UiState.Success(Unit)
            }.onFailure {
                _state.value = UiState.Error(it.message ?: "注册失败", it)
            }
        }
    }
}
