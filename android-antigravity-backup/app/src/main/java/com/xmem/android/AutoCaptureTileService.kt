package com.xmem.android

import android.content.Intent
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

class AutoCaptureTileService : TileService() {

    /**
     * 点击系统控制栏按钮时启动截屏流程。
     */
    override fun onClick() {
        val intent = Intent(this, CaptureActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivityAndCollapse(intent)
    }

    /**
     * 更新 Tile 状态为可用。
     */
    override fun onStartListening() {
        qsTile?.state = Tile.STATE_ACTIVE
        qsTile?.updateTile()
    }
}
