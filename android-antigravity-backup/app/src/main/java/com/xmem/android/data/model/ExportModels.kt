package com.xmem.android.data.model

data class NoteExportEstimateRequest(
    val export_type: String,
    val note_ids: List<Long>?,
    val include_all: Boolean
)

data class NoteExportEstimateResponse(
    val estimated_size: Long
)

data class NoteExportCreateRequest(
    val export_type: String,
    val note_ids: List<Long>?,
    val include_all: Boolean
)

data class NoteExportJob(
    val id: Long,
    val export_type: String,
    val status: String,
    val created_at: String
)
