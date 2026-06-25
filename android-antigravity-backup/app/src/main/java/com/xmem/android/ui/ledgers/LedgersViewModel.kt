package com.xmem.android.ui.ledgers

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmem.android.data.model.LedgerEntry
import com.xmem.android.data.repository.LedgerRepository
import com.xmem.android.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class LedgersViewModel @Inject constructor(private val repository: LedgerRepository) : ViewModel() {
    private val _state = MutableStateFlow<UiState<List<LedgerEntry>>>(UiState.Idle)
    val state: StateFlow<UiState<List<LedgerEntry>>> = _state

    init {
        fetchLedgers()
    }

    fun fetchLedgers(category: String? = null) {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                repository.fetchLedgers(1, 100, category).items
            }.onSuccess { items ->
                _state.value = UiState.Success(items)
            }.onFailure {
                _state.value = UiState.Error(it.message ?: "获取账本失败", it)
            }
        }
    }

    fun addLedger(text: String) {
        viewModelScope.launch {
            runCatching {
                repository.createLedger(text)
            }.onSuccess {
                fetchLedgers()
            }
        }
    }
}
