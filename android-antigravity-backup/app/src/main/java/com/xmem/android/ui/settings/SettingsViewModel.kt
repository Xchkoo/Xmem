package com.xmem.android.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmem.android.data.model.UserProfile
import com.xmem.android.data.repository.AuthRepository
import com.xmem.android.data.store.SessionStore
import com.xmem.android.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val sessionStore: SessionStore
) : ViewModel() {
    private val _profileState = MutableStateFlow<UiState<UserProfile>>(UiState.Idle)
    val profileState: StateFlow<UiState<UserProfile>> = _profileState

    var baseUrl: String
        get() = sessionStore.baseUrl
        set(value) {
            sessionStore.baseUrl = value
        }

    init {
        fetchProfile()
    }

    fun fetchProfile() {
        _profileState.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                authRepository.fetchProfile()
            }.onSuccess { profile ->
                _profileState.value = UiState.Success(profile)
                sessionStore.userName = profile.user_name ?: ""
            }.onFailure {
                _profileState.value = UiState.Error(it.message ?: "获取用户信息失败", it)
            }
        }
    }

    fun logout() {
        authRepository.logout()
    }
}
