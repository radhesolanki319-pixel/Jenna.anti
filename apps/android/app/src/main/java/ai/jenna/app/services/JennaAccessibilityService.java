package ai.jenna.app.services;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.graphics.Rect;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.ArrayList;
import java.util.List;

public class JennaAccessibilityService extends AccessibilityService {
    private static final String TAG = "JennaAccessibility";
    private static JennaAccessibilityService instance = null;

    public static JennaAccessibilityService getInstance() {
        return instance;
    }

    public static boolean isRunning() {
        return instance != null;
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        Log.i(TAG, "Jenna Autonomous Accessibility Engine Connected & Active");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;
        // Optionally capture screen state or focused elements for Antigravity & Hermes reasoning
    }

    @Override
    public void onInterrupt() {
        Log.w(TAG, "Jenna Accessibility Service Interrupted");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (instance == this) {
            instance = null;
        }
        Log.i(TAG, "Jenna Accessibility Service Destroyed");
    }

    /**
     * Finds a clickable view matching target text and clicks it.
     */
    public boolean performClickByText(String text) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;

        List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByText(text);
        if (nodes != null && !nodes.isEmpty()) {
            for (AccessibilityNodeInfo node : nodes) {
                if (node != null) {
                    if (clickNodeOrParent(node)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    /**
     * Finds a clickable view by resource-id and clicks it.
     */
    public boolean performClickById(String viewId) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;

        List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByViewId(viewId);
        if (nodes != null && !nodes.isEmpty()) {
            for (AccessibilityNodeInfo node : nodes) {
                if (node != null) {
                    if (clickNodeOrParent(node)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    private boolean clickNodeOrParent(AccessibilityNodeInfo node) {
        if (node == null) return false;
        if (node.isClickable()) {
            return node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
        }
        AccessibilityNodeInfo parent = node.getParent();
        if (parent != null) {
            return clickNodeOrParent(parent);
        }
        return false;
    }

    /**
     * Dispatches a tap gesture at coordinate (x, y).
     */
    public boolean dispatchTap(float x, float y) {
        Path path = new Path();
        path.moveTo(x, y);
        GestureDescription.Builder builder = new GestureDescription.Builder();
        GestureDescription.StrokeDescription stroke = new GestureDescription.StrokeDescription(path, 0, 50);
        builder.addStroke(stroke);
        return dispatchGesture(builder.build(), null, null);
    }

    /**
     * Dispatches a smooth swipe gesture from (startX, startY) to (endX, endY).
     */
    public boolean dispatchSwipe(float startX, float startY, float endX, float endY, long durationMs) {
        Path path = new Path();
        path.moveTo(startX, startY);
        path.lineTo(endX, endY);
        GestureDescription.Builder builder = new GestureDescription.Builder();
        GestureDescription.StrokeDescription stroke = new GestureDescription.StrokeDescription(path, 0, durationMs > 0 ? durationMs : 300);
        builder.addStroke(stroke);
        return dispatchGesture(builder.build(), null, null);
    }

    /**
     * Triggers hardware navigation actions (e.g. Back, Home, Notifications).
     */
    public boolean triggerGlobalAction(int actionId) {
        return performGlobalAction(actionId);
    }
}
