package com.xmem.android.data.repository

import com.xmem.android.data.model.LedgerBudget
import com.xmem.android.data.model.LedgerBudgetRequest
import com.xmem.android.data.model.LedgerCreateRequest
import com.xmem.android.data.model.LedgerEntry
import com.xmem.android.data.model.LedgerListResponse
import com.xmem.android.data.model.LedgerMonthlySummary
import com.xmem.android.data.model.LedgerStatistics
import com.xmem.android.data.model.LedgerUpdateRequest
import com.xmem.android.data.network.ApiService
import okhttp3.MultipartBody

class LedgerRepository(private val api: ApiService) {
    suspend fun fetchLedgers(page: Int, pageSize: Int, category: String?): LedgerListResponse {
        return api.fetchLedgers(page, pageSize, category)
    }

    suspend fun createLedger(text: String): LedgerEntry {
        return api.createLedger(LedgerCreateRequest(text = text))
    }

    suspend fun createLedgerWithImage(textPart: MultipartBody.Part?, imagePart: MultipartBody.Part): LedgerEntry {
        return api.createLedgerWithImage(textPart, imagePart)
    }

    suspend fun fetchLedger(id: Long): LedgerEntry = api.fetchLedger(id)

    suspend fun updateLedger(id: Long, payload: LedgerUpdateRequest): LedgerEntry {
        return api.updateLedger(id, payload)
    }

    suspend fun deleteLedger(id: Long) {
        api.deleteLedger(id)
    }

    suspend fun fetchStatistics(month: String?, year: Int?): LedgerStatistics {
        return api.fetchLedgerStatistics(month, year)
    }

    suspend fun generateSummary(month: String?): LedgerMonthlySummary {
        return api.generateLedgerSummary(month)
    }

    suspend fun fetchBudget(month: String?): LedgerBudget? {
        return api.fetchLedgerBudget(month)
    }

    suspend fun upsertBudget(month: String, amount: Double, currency: String): LedgerBudget {
        return api.upsertLedgerBudget(LedgerBudgetRequest(month, amount, currency))
    }
}
