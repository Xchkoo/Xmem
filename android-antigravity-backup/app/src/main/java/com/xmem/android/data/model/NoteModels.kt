package com.xmem.android.data.model

data class NoteFile(
    val name: String,
    val url: String,
    val size: Long
)

data class Note(
    val id: Long,
    val body_md: String,
    val ai_summary: String?,
    val is_ledger_note: Boolean?,
    val ledger_month: String?,
    val images: List<String>?,
    val files: List<NoteFile>?,
    val attachment_url: String?,
    val is_pinned: Boolean?,
    val is_shared: Boolean?,
    val share_uuid: String?,
    val created_at: String,
    val updated_at: String?
)

data class NoteCreateRequest(
    val body_md: String,
    val ai_summary: String?,
    val is_ledger_note: Boolean?,
    val ledger_month: String?
)

data class NoteUpdateRequest(
    val body_md: String
)

data class NoteShareStatus(
    val is_shared: Boolean,
    val note_uuid: String?,
    val share_user_id: Long,
    val share_url: String?
)

data class NoteAiSummary(
    val summary: String
)

data class NoteAiTodos(
    val todos: List<Todo>
)

data class SharedNoteUser(
    val id: Long,
    val email: String,
    val user_name: String?
)

data class SharedNote(
    val id: Long,
    val body_md: String,
    val images: List<String>?,
    val files: List<NoteFile>?,
    val is_pinned: Boolean?,
    val created_at: String,
    val updated_at: String,
    val share_user: SharedNoteUser,
    val can_edit: Boolean
)
