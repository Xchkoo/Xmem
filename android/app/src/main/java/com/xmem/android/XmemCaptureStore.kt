package com.xmem.android

import android.content.Context

/**
 * 原生侧保存的会话与开关。
 *
 * 之前 CaptureService 直接读 @capacitor/preferences 内部使用的 SharedPreferences，
 * 但那个插件用的文件名是 CapacitorStorage（不是 CapacitorPreferences），
 * 结果 token 永远读不到、上传必然 401。这里改用自建插件（A2）由 JS 主动下发，
 * 存储格式归我们自己的，不再依赖第三方插件的内部实现。
 */
object XmemCaptureStore {
    private const val PREFS_NAME = "xmem_capture"
    private const val KEY_TOKEN = "token"
    private const val KEY_BASE_URL = "base_url"
    private const val KEY_PREVIEW = "preview_enabled"
    private const val KEY_PENDING_LEDGER = "pending_ledger_id"

    const val DEFAULT_BASE_URL = "https://xmem.top/api"

    private fun prefs(context: Context) =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /** 登录成功后由 JS 下发，baseUrl 为空时回落到默认线上地址。 */
    fun saveSession(context: Context, token: String, baseUrl: String) {
        prefs(context).edit()
            .putString(KEY_TOKEN, token)
            .putString(KEY_BASE_URL, baseUrl.ifBlank { DEFAULT_BASE_URL })
            .apply()
    }

    /** 退出登录时清空，避免磁贴继续用旧 token 上传。 */
    fun clearSession(context: Context) {
        prefs(context).edit()
            .remove(KEY_TOKEN)
            .remove(KEY_BASE_URL)
            .apply()
    }

    fun token(context: Context): String = prefs(context).getString(KEY_TOKEN, "") ?: ""

    fun baseUrl(context: Context): String =
        prefs(context).getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL

    fun hasSession(context: Context): Boolean = token(context).isNotBlank()

    fun setPreviewEnabled(context: Context, enabled: Boolean) {
        prefs(context).edit().putBoolean(KEY_PREVIEW, enabled).apply()
    }

    fun isPreviewEnabled(context: Context): Boolean = prefs(context).getBoolean(KEY_PREVIEW, false)

    /** 上传成功后记下记账 id，App 回到前台时由 JS 读取并跳转详情。 */
    fun setPendingLedger(context: Context, ledgerId: Long) {
        prefs(context).edit().putLong(KEY_PENDING_LEDGER, ledgerId).apply()
    }

    /** 读取并清除待跳转的记账 id，没有则返回 0。 */
    fun consumePendingLedger(context: Context): Long {
        val prefs = prefs(context)
        val id = prefs.getLong(KEY_PENDING_LEDGER, 0L)
        if (id > 0L) {
            prefs.edit().remove(KEY_PENDING_LEDGER).apply()
        }
        return id
    }
}
