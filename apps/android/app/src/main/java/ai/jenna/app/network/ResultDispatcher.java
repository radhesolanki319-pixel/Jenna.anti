package ai.jenna.app.network;

public class ResultDispatcher implements Runnable {
    private final JennaCallback callback;
    private final String result;
    private final Throwable error;

    public ResultDispatcher(JennaCallback callback, String result, Throwable error) {
        this.callback = callback;
        this.result = result;
        this.error = error;
    }

    @Override
    public void run() {
        if (error != null) {
            callback.onError(error);
        } else {
            callback.onSuccess(result);
        }
    }
}
