package com.xmem.android.data.model

data class Todo(
    val id: Long,
    val title: String,
    val completed: Boolean,
    val is_pinned: Boolean?,
    val is_ai_generated: Boolean?,
    val group_id: Long?,
    val group_items: List<Todo>?,
    val created_at: String
)

data class TodoCreateRequest(
    val title: String,
    val group_id: Long?
)

data class TodoUpdateRequest(
    val title: String?,
    val completed: Boolean?
)
