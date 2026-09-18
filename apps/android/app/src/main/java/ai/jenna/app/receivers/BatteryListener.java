package ai.jenna.app.receivers;

public interface BatteryListener {
    void onBatteryUpdate(int level, float tempCelsius, boolean isCharging, boolean isBypassActive);
}
