package com.xmem.android

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/**
 * 把截图以 multipart 形式 POST 到 /ledger，走服务端既有的 OCR + LLM 记账链路。
 *
 * 失败重试 2 次（共 3 次尝试），仍失败则返回失败结果由调用方提示用户。
 */
object XmemLedgerUploader {

    data class Result(
        val ok: Boolean,
        val ledgerId: Long?,
        val message: String,
    )

    private const val MAX_ATTEMPTS = 3
    private const val RETRY_DELAY_MS = 1000L
    private const val CONNECT_TIMEOUT_MS = 10_000
    private const val READ_TIMEOUT_MS = 60_000

    fun upload(context: Context, file: File): Result {
        val token = XmemCaptureStore.token(context)
        if (token.isBlank()) {
            return Result(false, null, "未登录，请先打开 Xmem 登录")
        }
        val baseUrl = XmemCaptureStore.baseUrl(context).trimEnd('/')

        var lastError = "上传失败"
        repeat(MAX_ATTEMPTS) { attempt ->
            val result = attemptUpload("$baseUrl/ledger", token, file)
            if (result.ok) {
                return result
            }
            lastError = result.message
            // 凭证问题重试没有意义，直接返回
            if (result.message == MSG_UNAUTHORIZED) {
                return result
            }
            if (attempt < MAX_ATTEMPTS - 1) {
                Thread.sleep(RETRY_DELAY_MS)
            }
        }
        return Result(false, null, lastError)
    }

    private const val MSG_UNAUTHORIZED = "登录已过期，请重新登录"

    private fun attemptUpload(url: String, token: String, file: File): Result {
        val boundary = UUID.randomUUID().toString()
        var connection: HttpURLConnection? = null
        return try {
            connection = (URL(url).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                doInput = true
                connectTimeout = CONNECT_TIMEOUT_MS
                readTimeout = READ_TIMEOUT_MS
                setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
                setRequestProperty("Authorization", "Bearer $token")
            }

            connection.outputStream.use { output ->
                val lineEnd = "\r\n"
                val twoHyphens = "--"
                val header = StringBuilder()
                    .append(twoHyphens).append(boundary).append(lineEnd)
                    .append("Content-Disposition: form-data; name=\"image\"; filename=\"")
                    .append(file.name).append('"').append(lineEnd)
                    .append("Content-Type: image/png").append(lineEnd)
                    .append(lineEnd)
                    .toString()
                output.write(header.toByteArray())
                file.inputStream().use { input -> input.copyTo(output) }
                output.write(lineEnd.toByteArray())
                output.write(
                    (twoHyphens + boundary + twoHyphens + lineEnd).toByteArray()
                )
            }

            val code = connection.responseCode
            val body = (if (code in 200..299) connection.inputStream else connection.errorStream)
                ?.bufferedReader()?.use { it.readText() } ?: ""

            when {
                code == 401 || code == 403 -> Result(false, null, MSG_UNAUTHORIZED)
                code !in 200..299 -> Result(false, null, "服务器返回 $code")
                else -> parseSuccess(body)
            }
        } catch (error: Exception) {
            Result(false, null, error.message ?: "网络错误")
        } finally {
            connection?.disconnect()
        }
    }

    private fun parseSuccess(body: String): Result {
        return try {
            val json = JSONObject(body)
            val id = json.optLong("id", 0L).takeIf { it > 0L }
            val amount = json.optDouble("amount", Double.NaN)
            val category = json.optString("category", "").ifBlank { null }
            val parts = mutableListOf<String>()
            if (!amount.isNaN()) parts += "¥$amount"
            if (!category.isNullOrBlank()) parts += category
            val message = if (parts.isEmpty()) "已提交记账" else parts.joinToString(" ")
            Result(true, id, message)
        } catch (_: Exception) {
            // 只要 2xx 就算成功，解析失败不影响主流程
            Result(true, null, "已提交记账")
        }
    }
}
