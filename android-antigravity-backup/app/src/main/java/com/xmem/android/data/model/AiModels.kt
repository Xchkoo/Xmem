package com.xmem.android.data.model

data class ChatMessage(
    val role: String,
    val content: String
)

data class ChatContextNote(
    val id: Long,
    val body_md: String
)

data class ChatContextLedger(
    val id: Long,
    val raw_text: String,
    val amount: Double?,
    val category: String?
)

data class ChatContext(
    val notes: List<ChatContextNote>,
    val ledgers: List<ChatContextLedger>
)

data class ChatRequest(
    val messages: List<ChatMessage>,
    val context: ChatContext?
)

data class ChatResponse(
    val reply: String
)
