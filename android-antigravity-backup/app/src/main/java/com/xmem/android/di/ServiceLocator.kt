package com.xmem.android.di

import android.content.Context
import com.xmem.android.data.network.ApiClient
import com.xmem.android.data.network.ApiService
import com.xmem.android.data.repository.AuthRepository
import com.xmem.android.data.repository.ChatRepository
import com.xmem.android.data.repository.LedgerRepository
import com.xmem.android.data.repository.NoteRepository
import com.xmem.android.data.repository.StatisticsRepository
import com.xmem.android.data.repository.TodoRepository
import com.xmem.android.data.repository.ExportRepository
import com.xmem.android.data.store.SessionStore

object ServiceLocator {
    private lateinit var sessionStore: SessionStore

    fun init(context: Context) {
        sessionStore = SessionStore(context.applicationContext)
    }

    fun sessionStore(): SessionStore = sessionStore

    fun api(): ApiService = ApiClient.create(sessionStore)

    fun authRepository(): AuthRepository = AuthRepository(api(), sessionStore)

    fun noteRepository(): NoteRepository = NoteRepository(api())

    fun ledgerRepository(): LedgerRepository = LedgerRepository(api())

    fun todoRepository(): TodoRepository = TodoRepository(api())

    fun statisticsRepository(): StatisticsRepository = StatisticsRepository(api())

    fun exportRepository(): ExportRepository = ExportRepository(api())

    fun chatRepository(): ChatRepository = ChatRepository(api())
}
