package com.xmem.android.data.repository

import com.xmem.android.data.model.Note
import com.xmem.android.data.model.NoteAiSummary
import com.xmem.android.data.model.NoteAiTodos
import com.xmem.android.data.model.NoteCreateRequest
import com.xmem.android.data.model.NoteShareStatus
import com.xmem.android.data.model.NoteUpdateRequest
import com.xmem.android.data.model.SharedNote
import com.xmem.android.data.network.ApiService
import okhttp3.MultipartBody

class NoteRepository(private val api: ApiService) {
    suspend fun fetchNotes(query: String?): List<Note> = api.fetchNotes(query)

    suspend fun createNote(body: String, aiSummary: String?, isLedgerNote: Boolean?, ledgerMonth: String?): Note {
        return api.createNote(
            NoteCreateRequest(
                body_md = body,
                ai_summary = aiSummary,
                is_ledger_note = isLedgerNote,
                ledger_month = ledgerMonth
            )
        )
    }

    suspend fun updateNote(id: Long, body: String): Note {
        return api.updateNote(id, NoteUpdateRequest(body_md = body))
    }

    suspend fun deleteNote(id: Long) {
        api.deleteNote(id)
    }

    suspend fun uploadImage(part: MultipartBody.Part): String {
        return api.uploadNoteImage(part).url
    }

    suspend fun uploadFile(part: MultipartBody.Part): String {
        return api.uploadNoteFile(part).url
    }

    suspend fun createShare(id: Long): NoteShareStatus = api.createNoteShare(id)

    suspend fun toggleShare(id: Long, isShared: Boolean): NoteShareStatus {
        return api.toggleNoteShare(id, mapOf("is_shared" to isShared))
    }

    suspend fun fetchSharedNote(noteUuid: String, shareUserId: String): SharedNote {
        return api.fetchSharedNote(noteUuid, shareUserId)
    }

    suspend fun generateSummary(id: Long): NoteAiSummary = api.generateNoteSummary(id)

    suspend fun generateTodos(id: Long): NoteAiTodos = api.generateNoteTodos(id)

    suspend fun togglePin(id: Long): Note = api.toggleNotePin(id)
}
