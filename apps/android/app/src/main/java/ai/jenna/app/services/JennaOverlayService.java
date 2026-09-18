package ai.jenna.app.services;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.TextView;
import ai.jenna.app.R;
import ai.jenna.app.network.JennaApiClient;
import ai.jenna.app.network.JennaCallback;

public class JennaOverlayService extends Service implements View.OnTouchListener, JennaCallback, Runnable {
    public static final String ACTION_SHOW = "ai.jenna.app.SHOW_OVERLAY";
    public static final String ACTION_HIDE = "ai.jenna.app.HIDE_OVERLAY";
    public static final String ACTION_PULSE_POINTER = "ai.jenna.app.PULSE_POINTER";
    public static final String EXTRA_X = "extra_x";
    public static final String EXTRA_Y = "extra_y";
    public static final String EXTRA_BUBBLE_TEXT = "extra_bubble_text";

    private static boolean isShowing = false;
    private WindowManager windowManager;
    private View dexterView;
    private WindowManager.LayoutParams dexterParams;
    private TextView speechBubble;
    private final Handler handler = new Handler(Looper.getMainLooper());

    private int initialX;
    private int initialY;
    private float initialTouchX;
    private float initialTouchY;
    private long touchStartTime;

    public static boolean isOverlayShowing() {
        return isShowing;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        windowManager = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String action = intent.getAction();
            if (ACTION_HIDE.equals(action)) {
                hideDexterOverlay();
                stopSelf();
                return START_NOT_STICKY;
            } else if (ACTION_PULSE_POINTER.equals(action)) {
                float x = intent.getFloatExtra(EXTRA_X, 500f);
                float y = intent.getFloatExtra(EXTRA_Y, 800f);
                showPulsePointer(x, y);
                return START_STICKY;
            }
        }

        showDexterOverlay();
        if (intent != null && intent.hasExtra(EXTRA_BUBBLE_TEXT)) {
            setBubbleText(intent.getStringExtra(EXTRA_BUBBLE_TEXT));
        }
        return START_STICKY;
    }

    private void showDexterOverlay() {
        if (dexterView != null && isShowing) return;

        LayoutInflater inflater = LayoutInflater.from(this);
        dexterView = inflater.inflate(R.layout.overlay_dexter, null);
        speechBubble = dexterView.findViewById(R.id.dexter_speech_bubble);
        ImageView avatar = dexterView.findViewById(R.id.dexter_avatar);

        int overlayType = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;

        dexterParams = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                overlayType,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
        );

        dexterParams.gravity = Gravity.TOP | Gravity.START;
        dexterParams.x = 80;
        dexterParams.y = 350;

        avatar.setOnTouchListener(this);

        try {
            windowManager.addView(dexterView, dexterParams);
            isShowing = true;
            handler.postDelayed(this, 10000);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public boolean onTouch(View v, MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                initialX = dexterParams.x;
                initialY = dexterParams.y;
                initialTouchX = event.getRawX();
                initialTouchY = event.getRawY();
                touchStartTime = System.currentTimeMillis();
                return true;

            case MotionEvent.ACTION_MOVE:
                dexterParams.x = initialX + (int) (event.getRawX() - initialTouchX);
                dexterParams.y = initialY + (int) (event.getRawY() - initialTouchY);
                if (dexterView != null && dexterView.isAttachedToWindow()) {
                    windowManager.updateViewLayout(dexterView, dexterParams);
                }
                return true;

            case MotionEvent.ACTION_UP:
                long duration = System.currentTimeMillis() - touchStartTime;
                float diffX = Math.abs(event.getRawX() - initialTouchX);
                float diffY = Math.abs(event.getRawY() - initialTouchY);

                if (duration < 250 && diffX < 15 && diffY < 15) {
                    toggleSpeechBubble();
                }
                return true;
        }
        return false;
    }

    private void toggleSpeechBubble() {
        if (speechBubble == null) return;
        if (speechBubble.getVisibility() == View.VISIBLE) {
            speechBubble.setVisibility(View.GONE);
        } else {
            speechBubble.setVisibility(View.VISIBLE);
            JennaApiClient.fetchHermesDialogue(this);
        }
    }

    public void setBubbleText(String text) {
        if (speechBubble != null && text != null) {
            speechBubble.setText(text);
            speechBubble.setVisibility(View.VISIBLE);
        }
    }

    private void showPulsePointer(float x, float y) {
        try {
            LayoutInflater inflater = LayoutInflater.from(this);
            final View pointerView = inflater.inflate(R.layout.overlay_pointer, null);

            WindowManager.LayoutParams pointerParams = new WindowManager.LayoutParams(
                    WindowManager.LayoutParams.WRAP_CONTENT,
                    WindowManager.LayoutParams.WRAP_CONTENT,
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE,
                    PixelFormat.TRANSLUCENT
            );

            pointerParams.gravity = Gravity.TOP | Gravity.START;
            pointerParams.x = (int) x - 30;
            pointerParams.y = (int) y - 30;

            windowManager.addView(pointerView, pointerParams);

            pointerView.animate()
                    .scaleX(1.4f)
                    .scaleY(1.4f)
                    .alpha(0.0f)
                    .setDuration(1200)
                    .start();

            handler.postDelayed(new RemoveViewTask(windowManager, pointerView), 1250);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onSuccess(String text) {
        setBubbleText(text);
    }

    @Override
    public void onError(Throwable t) {
        setBubbleText("Jenna & Dexter 💖 Online");
    }

    @Override
    public void run() {
        if (isShowing && speechBubble != null && speechBubble.getVisibility() == View.VISIBLE) {
            JennaApiClient.fetchHermesDialogue(this);
        }
        handler.postDelayed(this, 15000);
    }

    private void hideDexterOverlay() {
        handler.removeCallbacks(this);
        if (dexterView != null && isShowing) {
            try {
                if (dexterView.isAttachedToWindow()) {
                    windowManager.removeView(dexterView);
                }
            } catch (Exception ignored) {}
            dexterView = null;
            isShowing = false;
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        hideDexterOverlay();
    }
}
