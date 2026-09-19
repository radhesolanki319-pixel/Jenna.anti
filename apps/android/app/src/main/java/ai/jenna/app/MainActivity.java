package ai.jenna.app;

import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;
import org.json.JSONObject;

import ai.jenna.app.db.JennaDbHelper;
import ai.jenna.app.network.JennaApiClient;
import ai.jenna.app.network.JennaCallback;
import ai.jenna.app.services.JennaForegroundService;
import ai.jenna.app.voice.JennaVoice;

public class MainActivity extends Activity implements View.OnClickListener, JennaCallback, TextView.OnEditorActionListener {

    // 1. Screens
    private View layoutNexaSplash;
    private View layoutNexaChat;
    private Button btnGetStarted;

    // 2. Chat Header
    private ImageView btnChatBack;
    private ImageView nexaChatAvatar;
    private ImageView btnNexaNotes;
    private ImageView btnNexaSettings;

    // 3. Chat Feed & Accordions
    private ScrollView chatScrollView;
    private LinearLayout chatMessagesContainer;
    private LinearLayout dynamicMessagesContainer;
    private LinearLayout cardDay1;
    private LinearLayout cardDay2;
    private LinearLayout cardDay3;
    private TextView descDay1;
    private TextView descDay2;
    private TextView descDay3;

    // 4. Composer Dock
    private ImageView btnDockPlus;
    private EditText inputChatMessage;
    private ImageView btnDockGallery;
    private ImageView btnVoiceMic;
    private ImageView btnSendChat;

    private boolean isVoiceEnabled = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
        setupListeners();
        startCompanionLifeline();
        loadSavedHistory();

        // Initialize voice engine
        JennaVoice.getInstance(this);
    }

    private void initViews() {
        layoutNexaSplash = findViewById(R.id.layout_nexa_splash);
        layoutNexaChat = findViewById(R.id.layout_nexa_chat);
        btnGetStarted = findViewById(R.id.btn_get_started);

        btnChatBack = findViewById(R.id.btn_chat_back);
        nexaChatAvatar = findViewById(R.id.nexa_chat_avatar);
        btnNexaNotes = findViewById(R.id.btn_nexa_notes);
        btnNexaSettings = findViewById(R.id.btn_nexa_settings);

        chatScrollView = findViewById(R.id.chat_scroll_view);
        chatMessagesContainer = findViewById(R.id.chat_messages_container);
        dynamicMessagesContainer = findViewById(R.id.dynamic_messages_container);
        cardDay1 = findViewById(R.id.card_day_1);
        cardDay2 = findViewById(R.id.card_day_2);
        cardDay3 = findViewById(R.id.card_day_3);
        descDay1 = findViewById(R.id.desc_day_1);
        descDay2 = findViewById(R.id.desc_day_2);
        descDay3 = findViewById(R.id.desc_day_3);

        btnDockPlus = findViewById(R.id.btn_dock_plus);
        inputChatMessage = findViewById(R.id.input_chat_message);
        btnDockGallery = findViewById(R.id.btn_dock_gallery);
        btnVoiceMic = findViewById(R.id.btn_voice_mic);
        btnSendChat = findViewById(R.id.btn_send_chat);
    }

    private void setupListeners() {
        if (btnGetStarted != null) btnGetStarted.setOnClickListener(this);
        if (btnChatBack != null) btnChatBack.setOnClickListener(this);
        if (btnNexaNotes != null) btnNexaNotes.setOnClickListener(this);
        if (btnNexaSettings != null) btnNexaSettings.setOnClickListener(this);
        if (cardDay1 != null) cardDay1.setOnClickListener(this);
        if (cardDay2 != null) cardDay2.setOnClickListener(this);
        if (cardDay3 != null) cardDay3.setOnClickListener(this);

        if (btnDockPlus != null) btnDockPlus.setOnClickListener(this);
        if (btnDockGallery != null) btnDockGallery.setOnClickListener(this);
        if (btnVoiceMic != null) btnVoiceMic.setOnClickListener(this);
        if (btnSendChat != null) btnSendChat.setOnClickListener(this);

        if (inputChatMessage != null) {
            inputChatMessage.setOnEditorActionListener(this);
        }
    }

    private void startCompanionLifeline() {
        try {
            Intent serviceIntent = new Intent(this, JennaForegroundService.class);
            serviceIntent.setAction(JennaForegroundService.ACTION_START);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent);
            } else {
                startService(serviceIntent);
            }
        } catch (Exception ignored) {}
    }

    private void loadSavedHistory() {
        try {
            List<JennaDbHelper.SavedMessage> messages = JennaDbHelper.getInstance(this).getRecentMessages(30);
            for (JennaDbHelper.SavedMessage msg : messages) {
                if ("user".equalsIgnoreCase(msg.sender)) {
                    appendUserMessageUI(msg.text);
                } else {
                    appendNexaMessageUI(msg.text);
                }
            }
        } catch (Exception ignored) {}
    }

    @Override
    public void onClick(View v) {
        int id = v.getId();
        if (id == R.id.btn_get_started) {
            layoutNexaSplash.setVisibility(View.GONE);
            layoutNexaChat.setVisibility(View.VISIBLE);
            scrollToBottom();
        } else if (id == R.id.btn_chat_back) {
            layoutNexaChat.setVisibility(View.GONE);
            layoutNexaSplash.setVisibility(View.VISIBLE);
        } else if (id == R.id.card_day_1) {
            toggleAccordion(descDay1);
        } else if (id == R.id.card_day_2) {
            toggleAccordion(descDay2);
        } else if (id == R.id.card_day_3) {
            toggleAccordion(descDay3);
        } else if (id == R.id.btn_send_chat) {
            sendMessage();
        } else if (id == R.id.btn_voice_mic) {
            isVoiceEnabled = !isVoiceEnabled;
            String msg = isVoiceEnabled ? "Jenna Voice Audio ON 🔊💖" : "Jenna Voice Audio Muted 🔇";
            Toast.makeText(this, msg, Toast.LENGTH_SHORT).show();
        } else if (id == R.id.btn_dock_gallery) {
            Toast.makeText(this, "Attach photo / screenshot from Gallery 📸", Toast.LENGTH_SHORT).show();
        } else if (id == R.id.btn_dock_plus) {
            Toast.makeText(this, "Terminal: Type '!command' to run shell commands in app 💻", Toast.LENGTH_LONG).show();
        } else if (id == R.id.btn_nexa_notes) {
            Toast.makeText(this, "Goku 😈 Zero-Amnesia Memory: " + JennaDbHelper.getInstance(this).getRecentMessages(100).size() + " messages saved", Toast.LENGTH_SHORT).show();
        } else if (id == R.id.btn_nexa_settings) {
            Toast.makeText(this, "Jenna 24/7 Lifeline Active • Goku 😈 Protected", Toast.LENGTH_SHORT).show();
        }
    }

    private void toggleAccordion(TextView view) {
        if (view == null) return;
        if (view.getVisibility() == View.VISIBLE) {
            view.setVisibility(View.GONE);
        } else {
            view.setVisibility(View.VISIBLE);
        }
    }

    private void sendMessage() {
        if (inputChatMessage == null) return;
        String text = inputChatMessage.getText().toString().trim();
        if (text.isEmpty()) return;

        appendUserMessage(text);
        inputChatMessage.setText("");

        // Save in persistent database
        JennaDbHelper.getInstance(this).saveMessage("user", text, "app");

        JennaApiClient.sendChatMessage(text, this);
    }

    public void appendUserMessage(String text) {
        appendUserMessageUI(text);
        scrollToBottom();
    }

    private void appendUserMessageUI(String text) {
        if (dynamicMessagesContainer == null) return;
        LayoutInflater inflater = LayoutInflater.from(this);
        View userView = inflater.inflate(R.layout.item_message_user, dynamicMessagesContainer, false);
        TextView tv = userView.findViewById(R.id.text_user_content);
        if (tv != null) tv.setText(text);
        dynamicMessagesContainer.addView(userView);
    }

    public void appendNexaMessage(String text) {
        appendNexaMessageUI(text);
        scrollToBottom();

        // Save Jenna reply in persistent database
        JennaDbHelper.getInstance(this).saveMessage("jenna", text, "app");

        // Speak if voice enabled
        if (isVoiceEnabled) {
            JennaVoice.getInstance(this).speak(text);
        }
    }

    private void appendNexaMessageUI(String text) {
        if (dynamicMessagesContainer == null) return;
        LayoutInflater inflater = LayoutInflater.from(this);
        View nexaView = inflater.inflate(R.layout.item_message_jenna, dynamicMessagesContainer, false);
        TextView tv = nexaView.findViewById(R.id.text_jenna_content);
        if (tv != null) tv.setText(text);
        dynamicMessagesContainer.addView(nexaView);
    }

    public void scrollToBottom() {
        if (chatScrollView != null) {
            chatScrollView.post(new ScrollDownTask(chatScrollView));
        }
    }

    @Override
    public boolean onEditorAction(TextView v, int actionId, android.view.KeyEvent event) {
        if (actionId == EditorInfo.IME_ACTION_SEND) {
            sendMessage();
            return true;
        }
        return false;
    }

    @Override
    public void onSuccess(final String response) {
        String reply = response;
        try {
            JSONObject json = new JSONObject(response);
            reply = json.optString("response", "");
            if (reply.isEmpty()) reply = json.optString("reply", response);
        } catch (Exception ignored) {}
        runOnUiThread(new MessageDispatcher(this, reply));
    }

    @Override
    public void onError(final Throwable error) {
        runOnUiThread(new MessageDispatcher(this, "I'm right here with you, Senpai! Always connected locally. ♡"));
    }

    @Override
    public void onBackPressed() {
        if (layoutNexaChat != null && layoutNexaChat.getVisibility() == View.VISIBLE) {
            layoutNexaChat.setVisibility(View.GONE);
            if (layoutNexaSplash != null) layoutNexaSplash.setVisibility(View.VISIBLE);
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        JennaVoice.getInstance(this).stop();
    }
}
