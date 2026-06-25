package com.xmem.android.data.repository

import com.xmem.android.data.model.NoteExportCreateRequest
import com.xmem.android.data.model.NoteExportEstimateRequest
import com.xmem.android.data.model.NoteExportEstimateResponse
import com.xmem.android.data.model.NoteExportJob
import com.xmem.android.data.network.ApiService
import okhttp3.ResponseBody

class ExportRepository(private val api: ApiService) {
    suspend fun fetchJobs(): List<NoteExportJob> = api.fetchNoteExports()

    suspend fun estimate(payload: NoteExportEstimateRequest): NoteExportEstimateResponse {
        return api.estimateNoteExport(payload)
    }

    suspend fun create(payload: NoteExportCreateRequest) {
        api.createNoteExport(payload)
    }

    suspend fun download(jobId: Long, type: String): ResponseBody {
        return api.downloadNoteExport(jobId, type)
    }

    suspend fun downloadChecksum(jobId: Long): ResponseBody {
        return api.downloadChecksumReport(jobId)
    }
}
