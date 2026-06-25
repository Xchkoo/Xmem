package com.xmem.android

import android.content.Intent
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

class AutoCaptureTileService : TileService() {

    override fun onClick() {
        val intent = Intent(this, CaptureActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivityAndCollapse(intent)
    }

    override fun onStartListening() {
        qsTile?.state = Tile.STATE_ACTIVE
        qsTile?.updateTile()
    }
}
