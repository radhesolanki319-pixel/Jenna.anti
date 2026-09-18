package ai.jenna.app.services;

import android.view.View;
import android.view.WindowManager;

public class RemoveViewTask implements Runnable {
    private final WindowManager windowManager;
    private final View view;

    public RemoveViewTask(WindowManager windowManager, View view) {
        this.windowManager = windowManager;
        this.view = view;
    }

    @Override
    public void run() {
        try {
            if (windowManager != null && view != null && view.isAttachedToWindow()) {
                windowManager.removeView(view);
            }
        } catch (Exception ignored) {}
    }
}
