package com.xmem.android.ui.ledgers

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmem.android.data.model.LedgerStatistics
import com.xmem.android.data.repository.LedgerRepository
import com.xmem.android.ui.common.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class LedgerStatisticsViewModel @Inject constructor(private val repository: LedgerRepository) : ViewModel() {
    private val _state = MutableStateFlow<UiState<LedgerStatistics>>(UiState.Idle)
    val state: StateFlow<UiState<LedgerStatistics>> = _state

    fun fetchStatistics(month: String? = null, year: Int? = null) {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                repository.fetchStatistics(month, year)
            }.onSuccess { stats ->
                _state.value = UiState.Success(stats)
            }.onFailure {
                _state.value = UiState.Error(it.message ?: "获取统计失败", it)
            }
        }
    }
}
