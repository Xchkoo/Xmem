package com.xmem.android.data.model

data class LedgerEntry(
    val id: Long,
    val raw_text: String,
    val amount: Double?,
    val category: String?,
    val currency: String,
    val status: String,
    val task_id: String?,
    val merchant: String?,
    val event_time: String?,
    val meta: Map<String, Any>?,
    val created_at: String,
    val updated_at: String?
)

data class LedgerListResponse(
    val items: List<LedgerEntry>,
    val total: Int,
    val page: Int,
    val page_size: Int,
    val total_pages: Int
)

data class LedgerCreateRequest(
    val text: String
)

data class LedgerUpdateRequest(
    val amount: Double?,
    val currency: String?,
    val category: String?,
    val merchant: String?,
    val raw_text: String?,
    val event_time: String?
)

data class LedgerBudget(
    val month: String,
    val amount: Double,
    val currency: String,
    val amount_cny: Double?
)

data class LedgerBudgetRequest(
    val month: String,
    val amount: Double,
    val currency: String
)

data class LedgerMonthlySummary(
    val summary: String
)
