package com.xmem.android.data.model

data class DailyStats(
    val date: String,
    val amount: Double,
    val count: Int
)

data class MonthlyStats(
    val month: String,
    val amount: Double,
    val count: Int
)

data class YearlyStats(
    val year: Int,
    val amount: Double,
    val count: Int
)

data class CategoryStats(
    val category: String,
    val amount: Double,
    val count: Int,
    val percentage: Double
)

data class LedgerStatistics(
    val current_month: String,
    val daily_data: List<DailyStats>,
    val monthly_data: List<MonthlyStats>,
    val yearly_data: List<MonthlyStats>,
    val yearly_totals: List<YearlyStats>,
    val category_stats: List<CategoryStats>,
    val current_month_total: Double,
    val last_month_total: Double,
    val month_diff: Double,
    val month_diff_percent: Double,
    val ai_summary: String?,
    val ledger_note_id: Long?,
    val budget: LedgerBudget?
)
