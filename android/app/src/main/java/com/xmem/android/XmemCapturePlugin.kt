package com.xmem.android

import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

/**
 * 前端与原生之间的桥：登录态下发、预览开关、以及「通知点开后要跳到哪笔账」。
 *
 * 之所以自建插件而不去读 @capacitor/preferences 的 SharedPreferences，
 * 是因为那属于第三方插件的内部存储格式，升级就可能变（这次就踩到了）。
 */
@CapacitorPlugin(name = "XmemCapture")
class XmemCapturePlugin : Plugin() {

    /** 登录成功后由 JS 调用，把 token 与 API 地址交给原生。 */
    @PluginMethod
    fun setSession(call: PluginCall) {
        val token = call.getString("token") ?: ""
        val baseUrl = call.getString("baseUrl") ?: ""
        if (token.isBlank()) {
            call.reject("token 不能为空")
            return
        }
        XmemCaptureStore.saveSession(context, token, baseUrl)
        call.resolve()
    }

    /** 退出登录时清空，避免磁贴继续用旧 token 上传。 */
    @PluginMethod
    fun clearSession(call: PluginCall) {
        XmemCaptureStore.clearSession(context)
        call.resolve()
    }

    /** 是否「截图后先在通知栏预览再上传」。 */
    @PluginMethod
    fun setPreviewEnabled(call: PluginCall) {
        val enabled = call.getBoolean("enabled") ?: false
        XmemCaptureStore.setPreviewEnabled(context, enabled)
        call.resolve()
    }

    /** App 启动/回到前台时读取当前状态，用于初始化设置开关。 */
    @PluginMethod
    fun getState(call: PluginCall) {
        val result = JSObject()
        result.put("hasSession", XmemCaptureStore.hasSession(context))
        result.put("previewEnabled", XmemCaptureStore.isPreviewEnabled(context))
        result.put("baseUrl", XmemCaptureStore.baseUrl(context))
        call.resolve(result)
    }

    /** 取出待跳转的记账 id（没有则为 0），读取后即清空。 */
    @PluginMethod
    fun consumePendingLedger(call: PluginCall) {
        val result = JSObject()
        result.put("ledgerId", XmemCaptureStore.consumePendingLedger(context))
        call.resolve(result)
    }
}
