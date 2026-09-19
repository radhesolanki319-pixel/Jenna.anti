package ai.jenna.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.StatFs;
import android.speech.RecognizerIntent;
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

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.json.JSONObject;

import ai.jenna.app.db.JennaDbHelper;
import ai.jenna.app.network.JennaApiClient;
import ai.jenna.app.services.JennaForegroundService;
import ai.jenna.app.services.JennaOverlayService;
import ai.jenna.app.terminal.ShellExecutor;
import ai.jenna.app.voice.JennaVoice;

public class MainActivity extends Activity implements View.OnClickListener, TextView.OnEditorActionListener, DialogInterface.OnClickListener {

    private static final int REQUEST_CODE_SPEECH = 1001;

    // Header Views
    private ImageView headerAvatar;
    private TextView textHeaderStatus;
    private Button btnQuickRefresh;
    private Button btnQuickDexter;
    private Button btnQuickTerminal;

    // Chips
    private Button chipStatus;
    private Button chipBattery;
    private Button chipStorage;
    private Button chipVoiceToggle;
    private Button chipClearChat;

    // Chat Area
    private ScrollView chatScrollView;
    private LinearLayout dynamicMessagesContainer;

    // Composer
    private ImageView btnVoiceMic;
    private EditText inputChatMessage;
    private ImageView btnSendChat;

    // State
    private boolean isVoiceEnabled = true;
    private boolean is144Hz = true;
    private TextView currentPendingView;
    private EditText terminalDialogInput;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
        setupListeners();
        startCompanionLifeline();
        loadSavedHistory();

        // Warm-up voice engine
        JennaVoice.getInstance(this);
    }

    private void initViews() {
        headerAvatar = findViewById(R.id.header_avatar);
        textHeaderStatus = findViewById(R.id.text_header_status);
        btnQuickRefresh = findViewById(R.id.btn_quick_refresh);
        btnQuickDexter = findViewById(R.id.btn_quick_dexter);
        btnQuickTerminal = findViewById(R.id.btn_quick_terminal);

        chipStatus = findViewById(R.id.chip_status);
        chipBattery = findViewById(R.id.chip_battery);
        chipStorage = findViewById(R.id.chip_storage);
        chipVoiceToggle = findViewById(R.id.chip_voice_toggle);
        chipClearChat = findViewById(R.id.chip_clear_chat);

        chatScrollView = findViewById(R.id.chat_scroll_view);
        dynamicMessagesContainer = findViewById(R.id.dynamic_messages_container);

        btnVoiceMic = findViewById(R.id.btn_voice_mic);
        inputChatMessage = findViewById(R.id.input_chat_message);
        btnSendChat = findViewById(R.id.btn_send_chat);
    }

    private void setupListeners() {
        btnQuickRefresh.setOnClickListener(this);
        btnQuickDexter.setOnClickListener(this);
        btnQuickTerminal.setOnClickListener(this);

        chipStatus.setOnClickListener(this);
        chipBattery.setOnClickListener(this);
        chipStorage.setOnClickListener(this);
        chipVoiceToggle.setOnClickListener(this);
        chipClearChat.setOnClickListener(this);

        btnVoiceMic.setOnClickListener(this);
        btnSendChat.setOnClickListener(this);
        inputChatMessage.setOnEditorActionListener(this);
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
            List<JennaDbHelper.SavedMessage> messages = JennaDbHelper.getInstance(this).getRecentMessages(40);
            if (messages.isEmpty()) {
                appendJennaMessageUI("System online, Boss! 🕶️⚡\nQualcomm Snapdragon 8 Gen 4 hardware governance active. Display locked at 144Hz. Bataiye, kya execute karna hai?");
            } else {
                for (JennaDbHelper.SavedMessage msg : messages) {
                    if ("user".equalsIgnoreCase(msg.sender)) {
                        appendUserMessageUI(msg.text);
                    } else {
                        appendJennaMessageUI(msg.text);
                    }
                }
            }
            scrollToBottom();
        } catch (Exception ignored) {}
    }

    @Override
    public void onClick(View v) {
        int id = v.getId();
        if (id == R.id.btn_send_chat) {
            sendMessage();
        } else if (id == R.id.btn_voice_mic) {
            startSpeechRecognition();
        } else if (id == R.id.btn_quick_refresh) {
            toggleRefreshRate();
        } else if (id == R.id.btn_quick_dexter) {
            toggleDexterOverlay();
        } else if (id == R.id.btn_quick_terminal) {
            showTerminalDialog();
        } else if (id == R.id.chip_status) {
            executeAndDisplayCommand("📊 System Diagnostics", "uptime && getprop ro.product.model");
        } else if (id == R.id.chip_battery) {
            executeAndDisplayCommand("🔋 Snapdragon Thermal & Battery", "dumpsys battery | grep -E 'level|temperature|status'");
        } else if (id == R.id.chip_storage) {
            displayStorageStats();
        } else if (id == R.id.chip_voice_toggle) {
            toggleVoice();
        } else if (id == R.id.chip_clear_chat) {
            dynamicMessagesContainer.removeAllViews();
            appendJennaMessageUI("Chat view cleared, Boss. Persistent memory intact on disk! 🛡️");
        }
    }

    private void sendMessage() {
        String text = inputChatMessage.getText().toString().trim();
        if (text.isEmpty()) return;

        inputChatMessage.setText("");
        appendUserMessageUI(text);
        JennaDbHelper.getInstance(this).saveMessage("user", text, "app");
        scrollToBottom();

        // Check if command
        if (text.startsWith("!") || text.startsWith("sh:")) {
            String cmd = text.replaceFirst("^(!|sh:)\\s*", "");
            executeAndDisplayCommand("💻 Terminal: " + cmd, cmd);
            return;
        }

        // Add pending view
        currentPendingView = appendPendingJennaMessageUI();
        scrollToBottom();

        JennaApiClient.sendChatMessage(text, new JennaApiHandler(this));
    }

    public void onApiSuccess(String result) {
        String reply = extractResponseText(result);
        if (currentPendingView != null) {
            currentPendingView.setText(reply);
        }
        JennaDbHelper.getInstance(this).saveMessage("jenna", reply, "app");
        scrollToBottom();

        if (isVoiceEnabled) {
            JennaVoice.getInstance(this).speak(reply);
        }
    }

    public void onApiError(String error) {
        String fallback = JennaApiClient.generateAutonomousReply(error);
        if (currentPendingView != null) {
            currentPendingView.setText(fallback);
        }
        JennaDbHelper.getInstance(this).saveMessage("jenna", fallback, "app");
        scrollToBottom();
    }

    private String extractResponseText(String jsonOrText) {
        if (jsonOrText == null) return "Directive received, Boss.";
        try {
            JSONObject obj = new JSONObject(jsonOrText);
            if (obj.has("response")) {
                return obj.getString("response");
            }
        } catch (Exception ignored) {}
        return jsonOrText;
    }

    private void startSpeechRecognition() {
        try {
            Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to Jenna...");
            startActivityForResult(intent, REQUEST_CODE_SPEECH);
        } catch (Exception e) {
            Toast.makeText(this, "Speech recognition: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_CODE_SPEECH && resultCode == RESULT_OK && data != null) {
            ArrayList<String> matches = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (matches != null && !matches.isEmpty()) {
                inputChatMessage.setText(matches.get(0));
                sendMessage();
            }
        }
    }

    private void toggleRefreshRate() {
        is144Hz = !is144Hz;
        int mode = is144Hz ? 1 : 0;
        String label = is144Hz ? "144.0 Hz" : "60.0 Hz";
        new Thread(new RefreshRateTask(this, mode, label)).start();
    }

    public void onRefreshRateToggled(boolean is144, String label) {
        btnQuickRefresh.setText(is144 ? "⚡ 144Hz" : "⚡ 60Hz");
        textHeaderStatus.setText("Snapdragon 8 Gen 4 • " + label);
        appendJennaMessageUI("Display refresh rate toggled: " + label + " ⚡");
        scrollToBottom();
    }

    private void toggleDexterOverlay() {
        try {
            Intent intent = new Intent(this, JennaOverlayService.class);
            if (JennaOverlayService.isOverlayShowing()) {
                intent.setAction(JennaOverlayService.ACTION_HIDE);
                startService(intent);
                btnQuickDexter.setText("🐾 HUD");
                appendJennaMessageUI("Dexter Floating HUD dismissed from screen.");
            } else {
                intent.setAction(JennaOverlayService.ACTION_SHOW);
                startService(intent);
                btnQuickDexter.setText("🐾 Active");
                appendJennaMessageUI("Dexter Floating HUD spawned onto screen! 🐾✨");
            }
            scrollToBottom();
        } catch (Exception e) {
            Toast.makeText(this, "Overlay error: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void showTerminalDialog() {
        terminalDialogInput = new EditText(this);
        terminalDialogInput.setHint("e.g. uname -a, ps, free -m");
        terminalDialogInput.setTextColor(getResources().getColor(R.color.text_primary));
        terminalDialogInput.setPadding(40, 30, 40, 30);

        new AlertDialog.Builder(this)
                .setTitle("💻 Shell Command Execution")
                .setView(terminalDialogInput)
                .setPositiveButton("Execute", this)
                .setNegativeButton("Cancel", null)
                .show();
    }

    @Override
    public void onClick(DialogInterface dialog, int which) {
        if (which == DialogInterface.BUTTON_POSITIVE && terminalDialogInput != null) {
            String cmd = terminalDialogInput.getText().toString().trim();
            if (!cmd.isEmpty()) {
                executeAndDisplayCommand("💻 Terminal: " + cmd, cmd);
            }
        }
    }

    private void executeAndDisplayCommand(String title, String command) {
        appendUserMessageUI("▶ " + title);
        TextView pending = appendPendingJennaMessageUI();
        scrollToBottom();
        new Thread(new CommandTask(this, command, pending)).start();
    }

    private void displayStorageStats() {
        try {
            File path = Environment.getDataDirectory();
            StatFs stat = new StatFs(path.getPath());
            long blockSize = stat.getBlockSizeLong();
            long totalBlocks = stat.getBlockCountLong();
            long availableBlocks = stat.getAvailableBlocksLong();
            long totalGB = (totalBlocks * blockSize) / (1024 * 1024 * 1024);
            long freeGB = (availableBlocks * blockSize) / (1024 * 1024 * 1024);

            String info = "💾 Storage Diagnostics:\n• Total Capacity: " + totalGB + " GB\n• Free Available: " + freeGB + " GB\n• Used: " + (totalGB - freeGB) + " GB";
            appendJennaMessageUI(info);
            scrollToBottom();
        } catch (Exception e) {
            appendJennaMessageUI("Storage check error: " + e.getMessage());
        }
    }

    private void toggleVoice() {
        isVoiceEnabled = !isVoiceEnabled;
        chipVoiceToggle.setText(isVoiceEnabled ? "🔊 Voice: ON" : "🔇 Voice: MUTED");
        Toast.makeText(this, isVoiceEnabled ? "Voice Notes Enabled 🔊" : "Voice Notes Muted 🔇", Toast.LENGTH_SHORT).show();
    }

    public void appendJennaMessage(String text) {
        appendJennaMessageUI(text);
        scrollToBottom();
    }

    public void appendUserMessage(String text) {
        appendUserMessageUI(text);
        scrollToBottom();
    }

    private void appendUserMessageUI(String text) {
        LayoutInflater inflater = LayoutInflater.from(this);
        View view = inflater.inflate(R.layout.item_message_user, dynamicMessagesContainer, false);
        TextView tv = view.findViewById(R.id.text_user_content);
        tv.setText(text);
        dynamicMessagesContainer.addView(view);
    }

    private void appendJennaMessageUI(String text) {
        LayoutInflater inflater = LayoutInflater.from(this);
        View view = inflater.inflate(R.layout.item_message_jenna, dynamicMessagesContainer, false);
        TextView tv = view.findViewById(R.id.text_jenna_content);
        tv.setText(text);
        dynamicMessagesContainer.addView(view);
    }

    private TextView appendPendingJennaMessageUI() {
        LayoutInflater inflater = LayoutInflater.from(this);
        View view = inflater.inflate(R.layout.item_message_jenna, dynamicMessagesContainer, false);
        TextView tv = view.findViewById(R.id.text_jenna_content);
        tv.setText("Thinking & processing directive...");
        dynamicMessagesContainer.addView(view);
        return tv;
    }

    private void scrollToBottom() {
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
    protected void onDestroy() {
        super.onDestroy();
        JennaVoice.getInstance(this).stop();
    }
}
