package ai.jenna.app;

import ai.jenna.app.terminal.ShellExecutor;

public class RefreshRateTask implements Runnable {
    private final MainActivity activity;
    private final int mode;
    private final String label;

    public RefreshRateTask(MainActivity activity, int mode, String label) {
        this.activity = activity;
        this.mode = mode;
        this.label = label;
    }

    @Override
    public void run() {
        ShellExecutor.execute("service call SurfaceFlinger 1035 i32 " + mode);
        if (activity != null) {
            activity.runOnUiThread(new RefreshRateUpdateTask(activity, mode == 1, label));
        }
    }
}
