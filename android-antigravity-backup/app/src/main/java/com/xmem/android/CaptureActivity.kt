package com.xmem.android

import android.app.Activity
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class CaptureActivity : AppCompatActivity() {

    private var projectionManager: MediaProjectionManager? = null

    /**
     * 请求系统截图授权并进入截屏流程。
     */
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_capture)
        projectionManager = getSystemService(MediaProjectionManager::class.java)
        startProjectionRequest()
    }

    /**
     * 发起截屏权限申请。
     */
    private fun startProjectionRequest() {
        val intent = projectionManager?.createScreenCaptureIntent()
        if (intent == null) {
            finish()
            return
        }
        startActivityForResult(intent, REQUEST_CODE_CAPTURE)
    }

    /**
     * 接收授权结果并交给前台服务处理。
     */
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != REQUEST_CODE_CAPTURE) {
            finish()
            return
        }
        if (resultCode != Activity.RESULT_OK || data == null) {
            finish()
            return
        }
        val serviceIntent = Intent(this, CaptureService::class.java).apply {
            putExtra(CaptureService.EXTRA_RESULT_CODE, resultCode)
            putExtra(CaptureService.EXTRA_DATA, data)
        }
        startForegroundService(serviceIntent)
        finish()
    }

    companion object {
        private const val REQUEST_CODE_CAPTURE = 1103
    }
}
