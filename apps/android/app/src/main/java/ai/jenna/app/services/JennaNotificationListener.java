package ai.jenna.app.services;

import android.app.Notification;
import android.app.PendingIntent;
import android.app.RemoteInput;
import android.content.Intent;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.util.Log;
import ai.jenna.app.db.JennaDbHelper;
import ai.jenna.app.network.JennaApiClient;
import ai.jenna.app.network.JennaCallback;
import org.json.JSONObject;

public class JennaNotificationListener extends NotificationListenerService {
    private static final String TAG = "JennaNotifListener";
    private static final String WHATSAPP_PKG = "com.whatsapp";
    private static final String WHATSAPP_BIZ_PKG = "com.whatsapp.w4b";

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null || sbn.getNotification() == null) return;

        String pkg = sbn.getPackageName();
        if (!WHATSAPP_PKG.equals(pkg) && !WHATSAPP_BIZ_PKG.equals(pkg)) {
            return;
        }

        Notification notification = sbn.getNotification();
        Bundle extras = notification.extras;
        if (extras == null) return;

        CharSequence titleChar = extras.getCharSequence(Notification.EXTRA_TITLE);
        CharSequence textChar = extras.getCharSequence(Notification.EXTRA_TEXT);
        if (titleChar == null || textChar == null) return;

        final String sender = titleChar.toString().trim();
        final String message = textChar.toString().trim();

        if (message.isEmpty() || sender.isEmpty() || sender.equalsIgnoreCase("WhatsApp")) {
            return;
        }

        // Check if there is an inline reply action
        final Notification.Action replyAction = findQuickReplyAction(notification);
        if (replyAction == null) return;

        Log.i(TAG, "Incoming WhatsApp message from: " + sender + " | text: " + message);

        // Save incoming message in database
        JennaDbHelper.getInstance(this).saveMessage(sender, message, "whatsapp");

        // Generate response via JennaApiClient using named callback
        JennaApiClient.sendChatMessage(message, new ReplyCallback(this, replyAction));
    }

    private Notification.Action findQuickReplyAction(Notification notification) {
        if (notification.actions == null) return null;
        for (Notification.Action action : notification.actions) {
            if (action.getRemoteInputs() != null) {
                for (RemoteInput remoteInput : action.getRemoteInputs()) {
                    if (remoteInput.getResultKey() != null) {
                        return action;
                    }
                }
            }
        }
        return null;
    }

    public void sendDirectReply(Notification.Action action, String replyText) {
        try {
            Intent intent = new Intent();
            Bundle bundle = new Bundle();
            for (RemoteInput remoteInput : action.getRemoteInputs()) {
                bundle.putCharSequence(remoteInput.getResultKey(), replyText);
            }
            RemoteInput.addResultsToIntent(action.getRemoteInputs(), intent, bundle);
            action.actionIntent.send(this, 0, intent);
            Log.i(TAG, "Sent native WhatsApp direct reply: " + replyText);
        } catch (PendingIntent.CanceledException e) {
            Log.e(TAG, "Reply PendingIntent canceled: " + e.getMessage());
        } catch (Exception e) {
            Log.e(TAG, "Failed to send WhatsApp reply: " + e.getMessage());
        }
    }

    public static class ReplyCallback implements JennaCallback {
        private final JennaNotificationListener service;
        private final Notification.Action action;

        public ReplyCallback(JennaNotificationListener service, Notification.Action action) {
            this.service = service;
            this.action = action;
        }

        @Override
        public void onSuccess(String response) {
            String reply = response;
            try {
                JSONObject json = new JSONObject(response);
                reply = json.optString("response", "");
                if (reply.isEmpty()) reply = json.optString("reply", response);
            } catch (Exception ignored) {}

            if (!reply.isEmpty()) {
                service.sendDirectReply(action, reply);
                JennaDbHelper.getInstance(service).saveMessage("jenna", reply, "whatsapp");
            }
        }

        @Override
        public void onError(Throwable error) {
            String fallback = "Ji Boss, maine message dekh liya! Goku phone se Antigravity companion active hai. Abhi check karti hu! 💖";
            service.sendDirectReply(action, fallback);
            JennaDbHelper.getInstance(service).saveMessage("jenna", fallback, "whatsapp");
        }
    }
}
