package ai.jenna.app;

import android.widget.TextView;
import ai.jenna.app.terminal.ShellExecutor;

public class CommandTask implements Runnable {
    private final MainActivity activity;
    private final String command;
    private final TextView targetView;

    public CommandTask(MainActivity activity, String command, TextView targetView) {
        this.activity = activity;
        this.command = command;
        this.targetView = targetView;
    }

    @Override
    public void run() {
        String output = ShellExecutor.execute(command);
        if (activity != null && targetView != null) {
            activity.runOnUiThread(new UpdateTextTask(targetView, output));
        }
    }
}
