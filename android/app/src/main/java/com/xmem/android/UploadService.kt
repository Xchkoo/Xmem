package com.xmem.android

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import java.io.File

/**
 * 只负责"把截图传到服务器"的前台服务，类型是 dataSync。
 *
 * 之前上传逻辑塞在 CaptureService 里，而那个服务声明的是 mediaProjection 类型：
 * Android 14+ 不允许在没有截屏会话的情况下启动该类型的服务（分享入口必然抛
 * SecurityException），"预览后上传"同样会崩。拆出来以后两条入口都能正常上传。
 */
class UploadService : Service() {

    private val handlerThread = HandlerThread("xmem-upload")
    private lateinit var handler: Handler
    private lateinit var notificationManager: NotificationManager
    private var foregroundStarted = false

    override fun onCreate() {
        super.onCreate()
        handlerThread.start()
        handler = Handler(handlerThread.looper)
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createChannels()
    }

    override fun onDestroy() {
        handlerThread.quitSafely()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val path = intent?.getStringExtra(EXTRA_IMAGE_PATH).orEmpty()

        // 没有会话时直接给结论，不发无意义的请求
        if (!XmemCaptureStore.hasSession(this)) {
            postResult(false, getString(R.string.need_login), null)
            stopSelf()
            return START_NOT_STICKY
        }

        startForegroundSafely()

        if (path.isBlank()) {
            postResult(false, getString(R.string.status_failed), null)
            stopSelf()
            return START_NOT_STICKY
        }

        handler.post { doUpload(File(path)) }
        return START_NOT_STICKY
    }

    /** 前台服务启动失败（权限/类型异常）时降级为普通通知，保证上传仍然执行。 */
    private fun startForegroundSafely() {
        try {
            startForeground(NOTIFICATION_ID, buildProgressNotification())
            foregroundStarted = true
        } catch (error: Exception) {
            foregroundStarted = false
            postResult(false, "无法启动上传服务：${error.message}", null)
        }
    }

    private fun doUpload(file: File) {
        val result = try {
            XmemLedgerUploader.upload(this, file)
        } catch (error: Exception) {
            XmemLedgerUploader.Result(false, null, error.message ?: "上传失败")
        }
        runCatching { file.delete() }
        postResult(result.ok, result.message, result.ledgerId)
        stopForegroundCompat()
        stopSelf()
    }

    private fun postResult(ok: Boolean, message: String, ledgerId: Long?) {
        if (ledgerId != null) {
            XmemCaptureStore.setPendingLedger(this, ledgerId)
        }
        val title = getString(if (ok) R.string.result_success else R.string.result_failed)
        val content = if (ok) {
            getString(R.string.result_success_body, message)
        } else {
            getString(R.string.result_failed_body, message)
        }

        val launch = Intent(this, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        val contentIntent = PendingIntent.getActivity(
            this,
            0,
            launch,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_RESULT)
            .setSmallIcon(R.drawable.ic_tile)
            .setContentTitle(title)
            .setContentText(content)
            .setStyle(NotificationCompat.BigTextStyle().bigText(content))
            .setContentIntent(contentIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()

        notificationManager.notify(RESULT_NOTIFICATION_ID, notification)
    }

    private fun buildProgressNotification() = NotificationCompat.Builder(this, CHANNEL_PROGRESS)
        .setSmallIcon(R.drawable.ic_tile)
        .setContentTitle(getString(R.string.action_capture))
        .setContentText(getString(R.string.status_upload))
        .setOngoing(true)
        .setPriority(NotificationCompat.PRIORITY_LOW)
        .build()

    private fun stopForegroundCompat() {
        if (!foregroundStarted) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        foregroundStarted = false
    }

    private fun createChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        notificationManager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_PROGRESS,
                getString(R.string.channel_upload_progress),
                NotificationManager.IMPORTANCE_LOW,
            )
        )
        notificationManager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_RESULT,
                getString(R.string.channel_capture_result),
                NotificationManager.IMPORTANCE_DEFAULT,
            )
        )
    }

    companion object {
        private const val EXTRA_IMAGE_PATH = "extra_image_path"
        private const val CHANNEL_PROGRESS = "xmem_upload_progress"
        private const val CHANNEL_RESULT = "xmem_capture_result"
        private const val NOTIFICATION_ID = 2003
        private const val RESULT_NOTIFICATION_ID = 2002

        /** 截屏与分享两条入口统一走这里。 */
        fun start(context: Context, imagePath: String) {
            val intent = Intent(context, UploadService::class.java)
                .putExtra(EXTRA_IMAGE_PATH, imagePath)
            ContextCompat.startForegroundService(context, intent)
        }
    }
}
