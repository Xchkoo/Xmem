package com.xmem.android

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import java.io.File
import java.io.FileOutputStream

/**
 * 路线 C：从系统分享菜单接收图片（截图后「分享」→ Xmem），直接走上传记账。
 *
 * 不需要截屏授权，作为磁贴之外零权限的兜底入口。
 */
class ShareCaptureActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val uri = extractStream(intent)
        if (uri == null) {
            finish()
            return
        }

        if (!XmemCaptureStore.hasSession(this)) {
            Toast.makeText(this, R.string.need_login, Toast.LENGTH_LONG).show()
            startActivity(
                Intent(this, MainActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            )
            finish()
            return
        }

        val file = copyToCache(uri)
        if (file == null) {
            Toast.makeText(this, R.string.share_copy_failed, Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        CaptureService.startUpload(this, file.absolutePath)
        Toast.makeText(this, R.string.share_received, Toast.LENGTH_SHORT).show()
        finish()
    }

    private fun extractStream(intent: Intent?): Uri? {
        if (intent == null) return null
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra(Intent.EXTRA_STREAM)
        }
    }

    private fun copyToCache(uri: Uri): File? {
        return try {
            val file = File(cacheDir, "xmem_share_${System.currentTimeMillis()}.png")
            contentResolver.openInputStream(uri)?.use { input ->
                FileOutputStream(file).use { output -> input.copyTo(output) }
            } ?: return null
            file
        } catch (_: Exception) {
            null
        }
    }
}
