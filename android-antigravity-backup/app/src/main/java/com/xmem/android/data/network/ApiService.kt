package com.xmem.android.data.network

import com.xmem.android.data.model.AuthRequest
import com.xmem.android.data.model.AuthResponse
import com.xmem.android.data.model.ChatRequest
import com.xmem.android.data.model.ChatResponse
import com.xmem.android.data.model.ChangePasswordRequest
import com.xmem.android.data.model.LedgerBudget
import com.xmem.android.data.model.LedgerBudgetRequest
import com.xmem.android.data.model.LedgerCreateRequest
import com.xmem.android.data.model.LedgerEntry
import com.xmem.android.data.model.LedgerListResponse
import com.xmem.android.data.model.LedgerMonthlySummary
import com.xmem.android.data.model.LedgerStatistics
import com.xmem.android.data.model.LedgerUpdateRequest
import com.xmem.android.data.model.Note
import com.xmem.android.data.model.NoteAiSummary
import com.xmem.android.data.model.NoteAiTodos
import com.xmem.android.data.model.NoteCreateRequest
import com.xmem.android.data.model.NoteExportCreateRequest
import com.xmem.android.data.model.NoteExportEstimateRequest
import com.xmem.android.data.model.NoteExportEstimateResponse
import com.xmem.android.data.model.NoteExportJob
import com.xmem.android.data.model.NoteShareStatus
import com.xmem.android.data.model.NoteUpdateRequest
import com.xmem.android.data.model.RegisterRequest
import com.xmem.android.data.model.SharedNote
import com.xmem.android.data.model.Todo
import com.xmem.android.data.model.TodoCreateRequest
import com.xmem.android.data.model.TodoUpdateRequest
import com.xmem.android.data.model.UserProfile
import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Streaming
import retrofit2.http.Part

interface ApiService {
    @POST("auth/login")
    suspend fun login(@Body payload: AuthRequest): AuthResponse

    @POST("auth/register")
    suspend fun register(@Body payload: RegisterRequest): AuthResponse

    @GET("auth/me")
    suspend fun fetchProfile(): UserProfile

    @POST("auth/change-password")
    suspend fun changePassword(@Body payload: ChangePasswordRequest)

    @GET("notes")
    suspend fun fetchNotes(@Query("q") query: String?): List<Note>

    @POST("notes")
    suspend fun createNote(@Body payload: NoteCreateRequest): Note

    @PATCH("notes/{id}")
    suspend fun updateNote(@Path("id") id: Long, @Body payload: NoteUpdateRequest): Note

    @DELETE("notes/{id}")
    suspend fun deleteNote(@Path("id") id: Long)

    @Multipart
    @POST("notes/upload-image")
    suspend fun uploadNoteImage(@Part file: MultipartBody.Part): UploadResponse

    @Multipart
    @POST("notes/upload-file")
    suspend fun uploadNoteFile(@Part file: MultipartBody.Part): UploadResponse

    @POST("notes/{id}/share")
    suspend fun createNoteShare(@Path("id") id: Long): NoteShareStatus

    @PATCH("notes/{id}/share-toggle")
    suspend fun toggleNoteShare(
        @Path("id") id: Long,
        @Body payload: Map<String, Boolean>
    ): NoteShareStatus

    @GET("notes/share")
    suspend fun fetchSharedNote(
        @Query("note_uuid") noteUuid: String,
        @Query("share_user_id") shareUserId: String
    ): SharedNote

    @POST("notes/{id}/ai-summary")
    suspend fun generateNoteSummary(@Path("id") id: Long): NoteAiSummary

    @POST("notes/{id}/ai-todos")
    suspend fun generateNoteTodos(@Path("id") id: Long): NoteAiTodos

    @PATCH("notes/{id}/pin")
    suspend fun toggleNotePin(@Path("id") id: Long): Note

    @GET("notes/exports")
    suspend fun fetchNoteExports(): List<NoteExportJob>

    @POST("notes/exports/estimate")
    suspend fun estimateNoteExport(@Body payload: NoteExportEstimateRequest): NoteExportEstimateResponse

    @POST("notes/exports")
    suspend fun createNoteExport(@Body payload: NoteExportCreateRequest)

    @Streaming
    @GET("notes/exports/{id}/{type}")
    suspend fun downloadNoteExport(
        @Path("id") id: Long,
        @Path("type") type: String
    ): ResponseBody

    @Streaming
    @GET("notes/exports/{id}/checksum-report")
    suspend fun downloadChecksumReport(@Path("id") id: Long): ResponseBody

    @GET("ledger")
    suspend fun fetchLedgers(
        @Query("page") page: Int,
        @Query("page_size") pageSize: Int,
        @Query("category") category: String?
    ): LedgerListResponse

    @POST("ledger")
    suspend fun createLedger(@Body payload: LedgerCreateRequest): LedgerEntry

    @Multipart
    @POST("ledger")
    suspend fun createLedgerWithImage(
        @Part("text") text: MultipartBody.Part?,
        @Part image: MultipartBody.Part
    ): LedgerEntry

    @GET("ledger/{id}")
    suspend fun fetchLedger(@Path("id") id: Long): LedgerEntry

    @PATCH("ledger/{id}")
    suspend fun updateLedger(@Path("id") id: Long, @Body payload: LedgerUpdateRequest): LedgerEntry

    @DELETE("ledger/{id}")
    suspend fun deleteLedger(@Path("id") id: Long)

    @GET("ledger/statistics")
    suspend fun fetchLedgerStatistics(
        @Query("month") month: String?,
        @Query("year") year: Int?
    ): LedgerStatistics

    @POST("ledger/statistics/ai-summary")
    suspend fun generateLedgerSummary(@Query("month") month: String?): LedgerMonthlySummary

    @GET("ledger/budget")
    suspend fun fetchLedgerBudget(@Query("month") month: String?): LedgerBudget?

    @PUT("ledger/budget")
    suspend fun upsertLedgerBudget(@Body payload: LedgerBudgetRequest): LedgerBudget

    @GET("todos")
    suspend fun fetchTodos(@Query("completed") completed: Boolean?): List<Todo>

    @POST("todos")
    suspend fun createTodo(@Body payload: TodoCreateRequest): Todo

    @PATCH("todos/{id}")
    suspend fun updateTodo(@Path("id") id: Long, @Body payload: TodoUpdateRequest): Todo

    @PATCH("todos/{id}/toggle")
    suspend fun toggleTodo(@Path("id") id: Long): Todo

    @PATCH("todos/{id}/pin")
    suspend fun toggleTodoPin(@Path("id") id: Long): Todo

    @DELETE("todos/{id}")
    suspend fun deleteTodo(@Path("id") id: Long)

    @POST("ai/chat")
    suspend fun chat(@Body payload: ChatRequest): ChatResponse
}

data class UploadResponse(
    val url: String
)
