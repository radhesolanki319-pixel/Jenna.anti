package ai.jenna.app;

import android.widget.TextView;

public class UpdateTextTask implements Runnable {
    private final TextView view;
    private final String text;

    public UpdateTextTask(TextView view, String text) {
        this.view = view;
        this.text = text;
    }

    @Override
    public void run() {
        if (view != null) {
            view.setText(text);
        }
    }
}
