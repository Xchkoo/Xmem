package com.xmem.android.data.repository

import com.xmem.android.data.model.LedgerStatistics
import com.xmem.android.data.network.ApiService

class StatisticsRepository(private val api: ApiService) {
    suspend fun fetchStatistics(month: String?): LedgerStatistics {
        return api.fetchLedgerStatistics(month, null)
    }
}
