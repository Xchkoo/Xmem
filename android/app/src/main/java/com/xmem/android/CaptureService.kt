package com.xmem.android

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.util.DisplayMetrics
import android.view.WindowManager
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream

/**
 * 截屏记账的核心流程：
 * 前台服务 → 注册 MediaProjection 回调 → 抓一帧 → 存 PNG →
 * （可选）通知栏预览并等待确认 → 上传 /ledger → 结果通知 → 自动停止。
 */
class CaptureService : Service() {

    private val handlerThread = HandlerThread("xmem-capture")
    private lateinit var handler: Handler
    private var mediaProjection: MediaProjection? = null
    private var imageReader: ImageReader? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var notificationManager: NotificationManager? = null
    private var capturedFile: File? = null
    private var busy = false

    /** Android 14 起必须先注册回调再 createVirtualDisplay，否则直接抛异常。 */
    private val projectionCallback = object : MediaProjection.Callback() {
        override fun onStop() {
            releaseProjection()
        }
    }

    /** 预览模式下超时自动取消，避免服务常驻。 */
    private val previewTimeout = Runnable { finishWithDelete() }

    override fun onCreate() {
        super.onCreate()
        handlerThread.start()
        handler = Handler(handlerThread.looper)
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannels()
    }

    override fun onDestroy() {
        handler.removeCallbacks(previewTimeout)
        releaseProjection()
        handlerThread.quitSafely()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CANCEL -> {
                finishWithDelete()
                return START_NOT_STICKY
            }

            ACTION_UPLOAD -> {
                // 用户点了通知里的「上传」
                val path = intent.getStringExtra(EXTRA_IMAGE_PATH)
                startForeground(NOTIFICATION_ID, buildStatusNotification(getString(R.string.status_upload)))
                if (path.isNullOrBlank()) {
                    finishWithDelete()
                } else {
                    handler.post { doUpload(File(path)) }
                }
                return START_NOT_STICKY
            }
        }

        if (busy) {
            // 上一次还在跑，忽略重复触发
            return START_NOT_STICKY
        }

        val resultCode = intent?.getIntExtra(EXTRA_RESULT_CODE, Activity.RESULT_CANCELED)
            ?: Activity.RESULT_CANCELED
        @Suppress("DEPRECATION")
        val data = intent?.getParcelableExtra<Intent>(EXTRA_DATA)
        val sharedImage = intent?.getStringExtra(EXTRA_IMAGE_PATH)

        startForeground(NOTIFICATION_ID, buildStatusNotification(getString(R.string.status_capture)))

        // 分享入口（路线 C）：图片已经在本地，直接走上传
        if (!sharedImage.isNullOrBlank()) {
            busy = true
            handler.post { doUpload(File(sharedImage)) }
            return START_NOT_STICKY
        }

        if (resultCode != Activity.RESULT_OK || data == null) {
            postResult(false, getString(R.string.status_failed), null)
            stopForegroundCompat()
            stopSelf()
            return START_NOT_STICKY
        }

        busy = true
        startCapture(resultCode, data)
        return START_NOT_STICKY
    }

    private fun startCapture(resultCode: Int, data: Intent) {
        val manager = getSystemService(MediaProjectionManager::class.java)
        val projection = manager?.getMediaProjection(resultCode, data) ?: run {
            postResult(false, getString(R.string.status_failed), null)
            stopForegroundCompat()
            stopSelf()
            return
        }
        mediaProjection = projection
        // 必须早于 createVirtualDisplay（Android 14+ 强制要求）
        projection.registerCallback(projectionCallback, handler)

        val metrics = DisplayMetrics()
        val windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val bounds = windowManager.currentWindowMetrics.bounds
            metrics.widthPixels = bounds.width()
            metrics.heightPixels = bounds.height()
            metrics.densityDpi = resources.displayMetrics.densityDpi
        } else {
            @Suppress("DEPRECATION")
            windowManager.defaultDisplay.getRealMetrics(metrics)
        }

        imageReader = ImageReader.newInstance(
            metrics.widthPixels,
            metrics.heightPixels,
            PixelFormat.RGBA_8888,
            2,
        )

        virtualDisplay = projection.createVirtualDisplay(
            "xmem-capture-display",
            metrics.widthPixels,
            metrics.heightPixels,
            metrics.densityDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface,
            null,
            handler,
        )

        // 等画面稳定再抓帧，避免拍到授权弹窗的残影或黑屏
        handler.postDelayed({ grabFrame() }, CAPTURE_DELAY_MS)
    }

    private fun grabFrame() {
        val reader = imageReader ?: return
        val image = try {
            reader.acquireLatestImage()
        } catch (_: Exception) {
            null
        }
        if (image == null) {
            handler.postDelayed({ grabFrame() }, 120)
            return
        }
        try {
            val bitmap = imageToBitmap(image)
            val file = saveBitmap(bitmap)
            capturedFile = file
            releaseProjection()

            if (XmemCaptureStore.isPreviewEnabled(this)) {
                showPreviewNotification(file, bitmap)
            } else {
                doUpload(file)
            }
        } catch (_: Exception) {
            postResult(false, getString(R.string.status_failed), null)
            stopForegroundCompat()
            stopSelf()
        } finally {
            image.close()
        }
    }

    private fun doUpload(file: File) {
        if (!file.exists()) {
            postResult(false, getString(R.string.status_failed), null)
            stopForegroundCompat()
            stopSelf()
            return
        }
        val result = XmemLedgerUploader.upload(this, file)
        runCatching { file.delete() }
        capturedFile = null
        postResult(result.ok, result.message, result.ledgerId)
        stopForegroundCompat()
        stopSelf()
    }

    private fun showPreviewNotification(file: File, bitmap: Bitmap) {
        handler.removeCallbacks(previewTimeout)
        handler.postDelayed(previewTimeout, PREVIEW_TIMEOUT_MS)

        val uploadIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, CaptureService::class.java)
                .setAction(ACTION_UPLOAD)
                .putExtra(EXTRA_IMAGE_PATH, file.absolutePath),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val cancelIntent = PendingIntent.getService(
            this,
            2,
            Intent(this, CaptureService::class.java).setAction(ACTION_CANCEL),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_STATUS)
            .setSmallIcon(R.drawable.ic_tile)
            .setContentTitle(getString(R.string.preview_title))
            .setContentText(getString(R.string.preview_text))
            .setStyle(
                NotificationCompat.BigPictureStyle()
                    .bigPicture(bitmap)
                    .bigLargeIcon(null as Bitmap?)
            )
            .setLargeIcon(bitmap)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .addAction(0, getString(R.string.action_upload), uploadIntent)
            .addAction(0, getString(R.string.action_cancel), cancelIntent)
            .build()

        notificationManager?.notify(NOTIFICATION_ID, notification)
    }

    private fun postResult(ok: Boolean, message: String, ledgerId: Long?) {
        if (ledgerId != null) {
            XmemCaptureStore.setPendingLedger(this, ledgerId)
        }
        val title = if (ok) getString(R.string.result_success) else getString(R.string.result_failed)
        val content = if (ok) {
            getString(R.string.result_success_body, message)
        } else {
            getString(R.string.result_failed_body, message)
        }

        val launch = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }
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

        ContextCompat.getSystemService(this, NotificationManager::class.java)
            ?.notify(RESULT_NOTIFICATION_ID, notification)
    }

    private fun finishWithDelete() {
        handler.removeCallbacks(previewTimeout)
        capturedFile?.let { runCatching { it.delete() } }
        capturedFile = null
        releaseProjection()
        stopForegroundCompat()
        stopSelf()
    }

    private fun stopForegroundCompat() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
    }

    private fun imageToBitmap(image: Image): Bitmap {
        val plane = image.planes.first()
        val buffer = plane.buffer
        val pixelStride = plane.pixelStride
        val rowStride = plane.rowStride
        val rowPadding = rowStride - pixelStride * image.width
        val bitmap = Bitmap.createBitmap(
            image.width + rowPadding / pixelStride,
            image.height,
            Bitmap.Config.ARGB_8888,
        )
        bitmap.copyPixelsFromBuffer(buffer)
        return Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height)
    }

    private fun saveBitmap(bitmap: Bitmap): File {
        val file = File(cacheDir, "xmem_shot_${System.currentTimeMillis()}.png")
        BufferedOutputStream(FileOutputStream(file)).use { stream ->
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)
        }
        return file
    }

    private fun releaseProjection() {
        runCatching { imageReader?.close() }
        imageReader = null
        runCatching { virtualDisplay?.release() }
        virtualDisplay = null
        runCatching { mediaProjection?.unregisterCallback(projectionCallback) }
        runCatching { mediaProjection?.stop() }
        mediaProjection = null
        busy = false
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val status = NotificationChannel(
            CHANNEL_STATUS,
            getString(R.string.channel_capture_status),
            NotificationManager.IMPORTANCE_LOW,
        )
        val result = NotificationChannel(
            CHANNEL_RESULT,
            getString(R.string.channel_capture_result),
            NotificationManager.IMPORTANCE_DEFAULT,
        )
        notificationManager?.createNotificationChannel(status)
        notificationManager?.createNotificationChannel(result)
    }

    private fun buildStatusNotification(content: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_STATUS)
            .setSmallIcon(R.drawable.ic_tile)
            .setContentTitle(getString(R.string.action_capture))
            .setContentText(content)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    companion object {
        const val ACTION_UPLOAD = "com.xmem.android.action.UPLOAD"
        const val ACTION_CANCEL = "com.xmem.android.action.CANCEL"
        const val EXTRA_RESULT_CODE = "extra_result_code"
        const val EXTRA_DATA = "extra_data"
        const val EXTRA_IMAGE_PATH = "extra_image_path"

        private const val CHANNEL_STATUS = "xmem_capture_status"
        private const val CHANNEL_RESULT = "xmem_capture_result"
        private const val NOTIFICATION_ID = 2001
        private const val RESULT_NOTIFICATION_ID = 2002
        private const val CAPTURE_DELAY_MS = 350L
        private const val PREVIEW_TIMEOUT_MS = 5 * 60 * 1000L

        /** 磁贴/分享入口统一的启动方法。 */
        fun startCapture(context: Context, resultCode: Int, data: Intent) {
            val intent = Intent(context, CaptureService::class.java).apply {
                putExtra(EXTRA_RESULT_CODE, resultCode)
                putExtra(EXTRA_DATA, data)
            }
            ContextCompat.startForegroundService(context, intent)
        }

        fun startUpload(context: Context, imagePath: String) {
            val intent = Intent(context, CaptureService::class.java).apply {
                setAction(ACTION_UPLOAD)
                putExtra(EXTRA_IMAGE_PATH, imagePath)
            }
            ContextCompat.startForegroundService(context, intent)
        }
    }
}
