package com.xmem.android

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
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
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

class CaptureService : Service() {

    private val handlerThread = HandlerThread("xmem-capture")
    private lateinit var handler: Handler
    private var mediaProjection: MediaProjection? = null
    private var imageReader: ImageReader? = null
    private var virtualDisplay: android.hardware.display.VirtualDisplay? = null
    private var notificationManager: NotificationManager? = null

    override fun onCreate() {
        super.onCreate()
        handlerThread.start()
        handler = Handler(handlerThread.looper)
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val resultCode = intent?.getIntExtra(EXTRA_RESULT_CODE, Activity.RESULT_CANCELED)
            ?: Activity.RESULT_CANCELED
        val data = intent?.getParcelableExtra<Intent>(EXTRA_DATA)

        startForeground(NOTIFICATION_ID, buildNotification(getString(R.string.status_capture)))

        if (resultCode != Activity.RESULT_OK || data == null) {
            updateNotification(getString(R.string.status_failed))
            stopSelf()
            return START_NOT_STICKY
        }
        startCapture(resultCode, data)
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        releaseProjection()
        handlerThread.quitSafely()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun startCapture(resultCode: Int, data: Intent) {
        val manager = getSystemService(MediaProjectionManager::class.java)
        val projection = manager?.getMediaProjection(resultCode, data) ?: run {
            updateNotification(getString(R.string.status_failed))
            stopSelf()
            return
        }
        mediaProjection = projection

        val metrics = DisplayMetrics()
        val windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        @Suppress("DEPRECATION")
        windowManager.defaultDisplay.getRealMetrics(metrics)

        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi

        imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2).apply {
            setOnImageAvailableListener({ reader ->
                handler.post {
                    val image = reader.acquireLatestImage()
                    if (image == null) {
                        return@post
                    }
                    handleImage(image)
                }
            }, handler)
        }

        virtualDisplay = projection.createVirtualDisplay(
            "xmem-capture-display",
            width,
            height,
            density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface,
            null,
            handler
        )
    }

    private fun handleImage(image: Image) {
        try {
            val bitmap = imageToBitmap(image)
            val file = saveBitmap(bitmap)
            updateNotification(getString(R.string.status_upload))
            val success = uploadImage(file)
            updateNotification(if (success) getString(R.string.status_done) else getString(R.string.status_failed))
        } catch (_: Exception) {
            updateNotification(getString(R.string.status_failed))
        } finally {
            image.close()
            releaseProjection()
            stopSelf()
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
            Bitmap.Config.ARGB_8888
        )
        bitmap.copyPixelsFromBuffer(buffer)
        return Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height)
    }

    private fun saveBitmap(bitmap: Bitmap): File {
        val file = File(cacheDir, "xmem_capture_${System.currentTimeMillis()}.png")
        BufferedOutputStream(FileOutputStream(file)).use { stream ->
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)
        }
        return file
    }

    private fun uploadImage(file: File): Boolean {
        val settings = loadUploadSettings()
        val baseUrl = settings.first
        val token = settings.second
        if (baseUrl.isBlank()) return false
        val url = URL(normalizeBaseUrl(baseUrl) + "/ledger")
        val boundary = UUID.randomUUID().toString()
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            doInput = true
            setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
            if (token.isNotBlank()) {
                setRequestProperty("Authorization", "Bearer $token")
            }
        }

        connection.outputStream.use { output ->
            val lineEnd = "\r\n"
            val twoHyphens = "--"
            val header = StringBuilder()
                .append(twoHyphens).append(boundary).append(lineEnd)
                .append("Content-Disposition: form-data; name=\"image\"; filename=\"${file.name}\"").append(lineEnd)
                .append("Content-Type: image/png").append(lineEnd)
                .append(lineEnd)
                .toString()
            output.write(header.toByteArray())
            file.inputStream().use { input ->
                input.copyTo(output)
            }
            output.write(lineEnd.toByteArray())
            val footer = StringBuilder()
                .append(twoHyphens).append(boundary).append(twoHyphens).append(lineEnd)
                .toString()
            output.write(footer.toByteArray())
        }

        val responseCode = connection.responseCode
        connection.disconnect()
        return responseCode in 200..299
    }

    private fun loadUploadSettings(): Pair<String, String> {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val baseUrl = prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL
        val token = prefs.getString(KEY_TOKEN, "") ?: ""
        return baseUrl to token
    }

    private fun normalizeBaseUrl(baseUrl: String): String {
        return if (baseUrl.endsWith("/")) baseUrl.dropLast(1) else baseUrl
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Xmem 截图上传",
                NotificationManager.IMPORTANCE_LOW
            )
            notificationManager?.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(content: String): Notification {
        return Notification.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.action_capture))
            .setContentText(content)
            .setSmallIcon(R.drawable.ic_tile)
            .setOngoing(true)
            .build()
    }

    private fun updateNotification(content: String) {
        val notification = buildNotification(content)
        notificationManager?.notify(NOTIFICATION_ID, notification)
    }

    private fun releaseProjection() {
        imageReader?.setOnImageAvailableListener(null, null)
        imageReader?.close()
        imageReader = null
        virtualDisplay?.release()
        virtualDisplay = null
        mediaProjection?.stop()
        mediaProjection = null
    }

    companion object {
        const val EXTRA_RESULT_CODE = "extra_result_code"
        const val EXTRA_DATA = "extra_data"
        private const val CHANNEL_ID = "xmem_capture_channel"
        private const val NOTIFICATION_ID = 2001
        private const val PREFS_NAME = "CapacitorPreferences"
        private const val KEY_BASE_URL = "baseUrl"
        private const val KEY_TOKEN = "token"
        private const val DEFAULT_BASE_URL = "https://xmem.top/api"
    }
}
