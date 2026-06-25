package com.xmem.android.di

import com.xmem.android.data.network.ApiService
import com.xmem.android.data.repository.*
import com.xmem.android.data.store.SessionStore
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule {

    @Provides
    @Singleton
    fun provideAuthRepository(
        apiService: ApiService,
        sessionStore: SessionStore
    ): AuthRepository = AuthRepository(apiService, sessionStore)

    @Provides
    @Singleton
    fun provideNoteRepository(
        apiService: ApiService
    ): NoteRepository = NoteRepository(apiService)

    @Provides
    @Singleton
    fun provideLedgerRepository(
        apiService: ApiService
    ): LedgerRepository = LedgerRepository(apiService)

    @Provides
    @Singleton
    fun provideTodoRepository(
        apiService: ApiService
    ): TodoRepository = TodoRepository(apiService)

    @Provides
    @Singleton
    fun provideStatisticsRepository(
        apiService: ApiService
    ): StatisticsRepository = StatisticsRepository(apiService)

    @Provides
    @Singleton
    fun provideChatRepository(
        apiService: ApiService
    ): ChatRepository = ChatRepository(apiService)

    @Provides
    @Singleton
    fun provideExportRepository(
        apiService: ApiService
    ): ExportRepository = ExportRepository(apiService)
}
