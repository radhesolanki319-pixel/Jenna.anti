package ai.jenna.app;

public class RefreshRateUpdateTask implements Runnable {
    private final MainActivity activity;
    private final boolean is144;
    private final String label;

    public RefreshRateUpdateTask(MainActivity activity, boolean is144, String label) {
        this.activity = activity;
        this.is144 = is144;
        this.label = label;
    }

    @Override
    public void run() {
        if (activity != null) {
            activity.onRefreshRateToggled(is144, label);
        }
    }
}
