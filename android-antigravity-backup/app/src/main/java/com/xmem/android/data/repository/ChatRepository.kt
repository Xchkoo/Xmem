package com.xmem.android.data.repository

import com.xmem.android.data.model.ChatRequest
import com.xmem.android.data.model.ChatResponse
import com.xmem.android.data.network.ApiService

class ChatRepository(private val api: ApiService) {
    suspend fun chat(request: ChatRequest): ChatResponse = api.chat(request)
}
