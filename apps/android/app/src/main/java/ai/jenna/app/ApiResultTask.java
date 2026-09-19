package ai.jenna.app;

public class ApiResultTask implements Runnable {
    private final MainActivity activity;
    private final String result;
    private final boolean isSuccess;

    public ApiResultTask(MainActivity activity, String result, boolean isSuccess) {
        this.activity = activity;
        this.result = result;
        this.isSuccess = isSuccess;
    }

    @Override
    public void run() {
        if (activity != null) {
            if (isSuccess) {
                activity.onApiSuccess(result);
            } else {
                activity.onApiError(result);
            }
        }
    }
}
