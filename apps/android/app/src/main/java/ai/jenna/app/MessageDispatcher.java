package ai.jenna.app;

public class MessageDispatcher implements Runnable {
    private final MainActivity activity;
    private final String message;

    public MessageDispatcher(MainActivity activity, String message) {
        this.activity = activity;
        this.message = message;
    }

    @Override
    public void run() {
        if (activity != null) {
            activity.addJennaMessage(message);
        }
    }
}
