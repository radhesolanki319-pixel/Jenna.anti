package ai.jenna.app;

import android.view.View;
import android.widget.ScrollView;

public class ScrollDownTask implements Runnable {
    private final ScrollView scrollView;

    public ScrollDownTask(ScrollView scrollView) {
        this.scrollView = scrollView;
    }

    @Override
    public void run() {
        if (scrollView != null) {
            scrollView.fullScroll(View.FOCUS_DOWN);
        }
    }
}
