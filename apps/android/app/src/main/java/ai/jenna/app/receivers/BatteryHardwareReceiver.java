package ai.jenna.app.receivers;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.BatteryManager;

public class BatteryHardwareReceiver extends BroadcastReceiver {

    private BatteryListener listener;

    public BatteryHardwareReceiver() {
    }

    public BatteryHardwareReceiver(BatteryListener listener) {
        this.listener = listener;
    }

    public void setListener(BatteryListener listener) {
        this.listener = listener;
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || !Intent.ACTION_BATTERY_CHANGED.equals(intent.getAction())) {
            return;
        }

        int rawLevel = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
        int scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
        int level = (rawLevel >= 0 && scale > 0) ? (rawLevel * 100) / scale : -1;

        int rawTemp = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0);
        float tempCelsius = rawTemp / 10.0f;

        int status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
        boolean isCharging = (status == BatteryManager.BATTERY_STATUS_CHARGING ||
                              status == BatteryManager.BATTERY_STATUS_FULL);

        int plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, -1);
        boolean isPlugged = (plugged == BatteryManager.BATTERY_PLUGGED_AC ||
                             plugged == BatteryManager.BATTERY_PLUGGED_USB ||
                             plugged == BatteryManager.BATTERY_PLUGGED_WIRELESS);

        boolean isBypassActive = isPlugged && (level >= 75 || tempCelsius < 36.0f);

        if (listener != null) {
            listener.onBatteryUpdate(level, tempCelsius, isCharging, isBypassActive);
        }
    }
}
