package ai.jenna.app.services;

import android.content.Intent;
import android.service.quicksettings.Tile;
import android.service.quicksettings.TileService;

public class JennaTileService extends TileService {

    @Override
    public void onStartListening() {
        super.onStartListening();
        updateTileState();
    }

    @Override
    public void onClick() {
        super.onClick();
        Intent intent = new Intent(this, JennaOverlayService.class);
        if (JennaOverlayService.isOverlayShowing()) {
            intent.setAction(JennaOverlayService.ACTION_HIDE);
        } else {
            intent.setAction(JennaOverlayService.ACTION_SHOW);
        }
        startService(intent);

        // Update tile after toggle
        updateTileState();
    }

    private void updateTileState() {
        Tile tile = getQsTile();
        if (tile == null) return;

        boolean active = JennaOverlayService.isOverlayShowing();
        tile.setState(active ? Tile.STATE_ACTIVE : Tile.STATE_INACTIVE);
        tile.setLabel("Jenna AI");
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            tile.setSubtitle(active ? "Dexter Visible" : "Dexter Hidden");
        }
        tile.updateTile();
    }
}
