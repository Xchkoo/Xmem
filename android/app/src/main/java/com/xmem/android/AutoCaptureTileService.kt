package com.xmem.android

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

/**
 * 快捷设置面板里的「自动记账」开关。
 *
 * Android 14 起 startActivityAndCollapse(Intent) 已废弃，新系统必须用 PendingIntent 重载，
 * 否则点击可能没有反应。
 */
class AutoCaptureTileService : TileService() {

    override fun onClick() {
        val intent = Intent(this, CaptureActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            val pending = PendingIntent.getActivity(
                this,
                0,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
            startActivityAndCollapse(pending)
        } else {
            @Suppress("DEPRECATION")
            startActivityAndCollapse(intent)
        }
    }

    override fun onStartListening() {
        val tile = qsTile ?: return
        // 没登录时置灰，提示用户先打开 App
        tile.state = if (XmemCaptureStore.hasSession(this)) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        tile.label = getString(R.string.tile_label)
        tile.updateTile()
    }
}
