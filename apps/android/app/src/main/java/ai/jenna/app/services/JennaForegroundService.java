package ai.jenna.app.services;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.IBinder;
import android.os.PowerManager;
import android.util.Log;
import ai.jenna.app.MainActivity;
import ai.jenna.app.R;
import ai.jenna.app.network.JennaApiClient;
import ai.jenna.app.network.JennaCallback;
import ai.jenna.app.receivers.BatteryHardwareReceiver;
import ai.jenna.app.receivers.BatteryListener;
import org.json.JSONObject;

public class JennaForegroundService extends Service implements BatteryListener, JennaCallback {
    private static final String TAG = "JennaForegroundService";
    private static final String CHANNEL_ID = "jenna_lifeline_channel";
    private static final int NOTIFICATION_ID = 2026;

    public static final String ACTION_START = "ai.jenna.app.START_LIFELINE";
    public static final String ACTION_STOP = "ai.jenna.app.STOP_LIFELINE";
    public static final String ACTION_TOGGLE_DEXTER = "ai.jenna.app.ACTION_TOGGLE_DEXTER";

    private static boolean isRunning = false;
    private PowerManager.WakeLock wakeLock;
    private BatteryHardwareReceiver batteryReceiver;

    public static boolean isServiceRunning() {
        return isRunning;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        acquireWakeLock();
        registerBatteryMonitoring();
        isRunning = true;
        Log.i(TAG, "Jenna 24/7 Lifeline Daemon started");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String action = intent.getAction();
            if (ACTION_STOP.equals(action)) {
                stopForeground(true);
                stopSelf();
                return START_NOT_STICKY;
            } else if (ACTION_TOGGLE_DEXTER.equals(action)) {
                Intent overlayIntent = new Intent(this, JennaOverlayService.class);
                if (JennaOverlayService.isOverlayShowing()) {
                    overlayIntent.setAction(JennaOverlayService.ACTION_HIDE);
                } else {
                    overlayIntent.setAction(JennaOverlayService.ACTION_SHOW);
                }
                startService(overlayIntent);
            }
        }

        Notification notification = buildNotification("Jenna Lifeline Active — Antigravity & Hermes Governed");
        startForeground(NOTIFICATION_ID, notification);

        return START_STICKY;
    }

    private void createNotificationChannel() {
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Jenna AI 24/7 Lifeline",
                NotificationManager.IMPORTANCE_LOW
        );
        channel.setDescription("Maintains Jenna's continuous hardware governance & Dex pet");
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) {
            manager.createNotificationChannel(channel);
        }
    }

    private Notification buildNotification(String text) {
        Intent contentIntent = new Intent(this, MainActivity.class);
        PendingIntent contentPendingIntent = PendingIntent.getActivity(
                this, 0, contentIntent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Intent toggleIntent = new Intent(this, JennaForegroundService.class);
        toggleIntent.setAction(ACTION_TOGGLE_DEXTER);
        PendingIntent togglePendingIntent = PendingIntent.getService(
                this, 1, toggleIntent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Intent stopIntent = new Intent(this, JennaForegroundService.class);
        stopIntent.setAction(ACTION_STOP);
        PendingIntent stopPendingIntent = PendingIntent.getService(
                this, 2, stopIntent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification.Builder builder = new Notification.Builder(this, CHANNEL_ID)
                .setContentTitle(getString(R.string.foreground_service_title))
                .setContentText(text)
                .setSmallIcon(R.drawable.ic_launcher)
                .setContentIntent(contentPendingIntent)
                .setOngoing(true)
                .addAction(new Notification.Action.Builder(null, "Toggle Dexter", togglePendingIntent).build())
                .addAction(new Notification.Action.Builder(null, "Stop", stopPendingIntent).build());

        return builder.build();
    }

    private void acquireWakeLock() {
        try {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            if (pm != null && wakeLock == null) {
                wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Jenna::LifelineWakeLock");
                wakeLock.acquire(12 * 60 * 60 * 1000L);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error acquiring WakeLock: " + e.getMessage());
        }
    }

    private void registerBatteryMonitoring() {
        batteryReceiver = new BatteryHardwareReceiver(this);
        IntentFilter filter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        registerReceiver(batteryReceiver, filter);
    }

    @Override
    public void onBatteryUpdate(int level, float tempCelsius, boolean isCharging, boolean isBypassActive) {
        try {
            JSONObject payload = new JSONObject();
            payload.put("battery_level", level);
            payload.put("battery_temp", tempCelsius);
            payload.put("charging", isCharging);
            payload.put("bypass_active", isBypassActive);

            JennaApiClient.postTelemetry(payload, this);
        } catch (Exception ignored) {}
    }

    @Override
    public void onSuccess(String result) {}

    @Override
    public void onError(Throwable t) {}

    @Override
    public void onDestroy() {
        super.onDestroy();
        isRunning = false;

        if (batteryReceiver != null) {
            try {
                unregisterReceiver(batteryReceiver);
            } catch (Exception ignored) {}
            batteryReceiver = null;
        }

        if (wakeLock != null && wakeLock.isHeld()) {
            try {
                wakeLock.release();
            } catch (Exception ignored) {}
            wakeLock = null;
        }

        Log.i(TAG, "Jenna Foreground Service Stopped");
    }
}
