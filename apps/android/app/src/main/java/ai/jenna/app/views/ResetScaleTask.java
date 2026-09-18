package ai.jenna.app.views;

import android.view.View;

public class ResetScaleTask implements Runnable {
    private final View view;

    public ResetScaleTask(View view) {
        this.view = view;
    }

    @Override
    public void run() {
        if (view != null) {
            view.animate().scaleX(1.0f).scaleY(1.0f).setDuration(150);
        }
    }
}
