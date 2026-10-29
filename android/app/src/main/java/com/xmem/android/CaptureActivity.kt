package com.xmem.android

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

/**
 * 磁贴点击后的入口：确认已登录 → 申请通知权限（Android 13+）→ 申请截屏授权 → 交给 CaptureService。
 *
 * 注意：截屏授权每次都必须由系统弹窗确认，这是 MediaProjection 的硬性限制，代码无法绕过。
 */
class CaptureActivity : AppCompatActivity() {

    private val projectionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val data = result.data
        if (result.resultCode == RESULT_OK && data != null) {
            CaptureService.startCapture(this, result.resultCode, data)
        } else {
            Toast.makeText(this, R.string.capture_cancelled, Toast.LENGTH_SHORT).show()
        }
        finish()
    }

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { requestProjection() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_capture)

        if (!XmemCaptureStore.hasSession(this)) {
            Toast.makeText(this, R.string.need_login, Toast.LENGTH_LONG).show()
            startActivity(
                Intent(this, MainActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            )
            finish()
            return
        }

        // Android 13+ 没有通知权限时结果通知不显示，先申请一次
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        } else {
            requestProjection()
        }
    }

    private fun requestProjection() {
        val manager = getSystemService(MediaProjectionManager::class.java)
        val intent = manager?.createScreenCaptureIntent()
        if (intent == null) {
            Toast.makeText(this, R.string.status_failed, Toast.LENGTH_SHORT).show()
            finish()
            return
        }
        projectionLauncher.launch(intent)
    }
}
