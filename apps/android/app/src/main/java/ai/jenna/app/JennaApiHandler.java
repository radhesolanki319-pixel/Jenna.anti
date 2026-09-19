package ai.jenna.app;

import ai.jenna.app.network.JennaCallback;

public class JennaApiHandler implements JennaCallback {
    private final MainActivity activity;

    public JennaApiHandler(MainActivity activity) {
        this.activity = activity;
    }

    @Override
    public void onSuccess(String result) {
        if (activity != null) {
            activity.runOnUiThread(new ApiResultTask(activity, result, true));
        }
    }

    @Override
    public void onError(Throwable error) {
        if (activity != null) {
            String msg = error != null ? error.getMessage() : "Network error";
            activity.runOnUiThread(new ApiResultTask(activity, msg, false));
        }
    }
}
