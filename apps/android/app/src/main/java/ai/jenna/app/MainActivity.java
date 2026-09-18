package ai.jenna.app;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
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

import org.json.JSONObject;

import ai.jenna.app.network.JennaApiClient;
import ai.jenna.app.network.JennaCallback;
import ai.jenna.app.receivers.BatteryHardwareReceiver;
import ai.jenna.app.receivers.BatteryListener;
import ai.jenna.app.services.JennaAccessibilityService;
import ai.jenna.app.services.JennaForegroundService;
import ai.jenna.app.services.JennaOverlayService;
import ai.jenna.app.views.AiOrbView;
import ai.jenna.app.views.AudioWaveformView;
import ai.jenna.app.views.BypassFlowView;
import ai.jenna.app.views.CircularGaugeView;
import ai.jenna.app.views.ResetScaleTask;

public class MainActivity extends Activity implements View.OnClickListener, BatteryListener, JennaCallback, Runnable, TextView.OnEditorActionListener {
    private static final int REQ_OVERLAY_PERMISSION = 101;
    private static final int REQ_NOTIF_PERMISSION = 102;

    // 1. Header Bar
    private ImageView headerAvatar;
    private TextView headerBatteryBadge;
    private ImageView btnHeaderDexter;

    // 1.1 Living Companion Split Dashboard Elements
    private ImageView characterAvatarStage;
    private TextView textCompanionSubtitle;
    private AudioWaveformView companionAudioWave;
    private CircularGaugeView gaugeDashCpu;
    private CircularGaugeView gaugeDashBattery;
    private LinearLayout cardDashDexter;

    // 2. Screens
    private View screenChat;
    private View screenDexter;
    private View screenCyber;
    private View screenSoul;

    // 3. Bottom Navigation
    private LinearLayout navChat;
    private LinearLayout navDexter;
    private LinearLayout navCyber;
    private LinearLayout navSoul;
    private TextView textNavChat;
    private TextView textNavDexter;
    private TextView textNavCyber;
    private TextView textNavSoul;

    // 4. Chat Screen Elements
    private ScrollView chatScrollView;
    private LinearLayout chatMessagesContainer;
    private EditText inputChatMessage;
    private ImageView btnSendChat;
    private ImageView btnVoiceMic;
    private TextView chipHowAreYou;
    private TextView chipSpawnDexter;
    private TextView chipPulsePointer;
    private TextView chipCheckBattery;
    private TextView chipOpenWeb;

    // 5. Dexter Studio Screen Elements
    private Button btnToggleDexterMain;
    private Button btnPulsePointerMain;
    private TextView textDexterStatusDesc;
    private Button btnDexterSayProtect;
    private Button btnDexterSaySleep;
    private Button btnDexterSayCool;

    // 6. CyberDeck Screen Elements
    private CircularGaugeView gaugeBattery;
    private CircularGaugeView gaugeTemperature;
    private BypassFlowView bypassFlowView;
    private TextView textBypassBadge;
    private Button btnToggleLifelineHub;
    private Button btnAccessibilityHub;
    private Button btnPingBrainHub;
    private Button btnOpenWebHub;

    // Hardware State
    private BatteryHardwareReceiver batteryReceiver;
    private int currentBatteryLevel = 24;
    private float currentBatteryTemp = 36.6f;
    private String currentBypassState = "ON BATTERY";
    private int currentTab = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
        setupListeners();
        switchTab(0);
        checkPermissions();
    }

    private void initViews() {
        // Header
        headerAvatar = findViewById(R.id.header_avatar);
        headerBatteryBadge = findViewById(R.id.header_battery_badge);
        btnHeaderDexter = findViewById(R.id.btn_header_dexter);

        // Screens
        screenChat = findViewById(R.id.screen_chat);
        screenDexter = findViewById(R.id.screen_dexter);
        screenCyber = findViewById(R.id.screen_cyber);
        screenSoul = findViewById(R.id.screen_soul);

        // Bottom Nav
        navChat = findViewById(R.id.nav_chat);
        navDexter = findViewById(R.id.nav_dexter);
        navCyber = findViewById(R.id.nav_cyber);
        navSoul = findViewById(R.id.nav_soul);
        textNavChat = findViewById(R.id.text_nav_chat);
        textNavDexter = findViewById(R.id.text_nav_dexter);
        textNavCyber = findViewById(R.id.text_nav_cyber);
        textNavSoul = findViewById(R.id.text_nav_soul);

        // Chat & Living Companion Stage
        characterAvatarStage = findViewById(R.id.character_avatar_stage);
        textCompanionSubtitle = findViewById(R.id.text_companion_subtitle);
        companionAudioWave = findViewById(R.id.companion_audio_wave);
        gaugeDashCpu = findViewById(R.id.gauge_dash_cpu);
        gaugeDashBattery = findViewById(R.id.gauge_dash_battery);
        cardDashDexter = findViewById(R.id.card_dash_dexter);

        if (gaugeDashCpu != null) {
            gaugeDashCpu.setData(68f, "3.36GHz", "SD 8 GEN 2", 0xFFF59E0B);
        }
        if (gaugeDashBattery != null) {
            gaugeDashBattery.setData(84f, "84%", "BYPASS", 0xFF10B981);
        }

        chatScrollView = findViewById(R.id.chat_scroll_view);
        chatMessagesContainer = findViewById(R.id.chat_messages_container);
        inputChatMessage = findViewById(R.id.input_chat_message);
        btnSendChat = findViewById(R.id.btn_send_chat);
        btnVoiceMic = findViewById(R.id.btn_voice_mic);

        chipHowAreYou = findViewById(R.id.chip_how_are_you);
        chipSpawnDexter = findViewById(R.id.chip_spawn_dexter);
        chipPulsePointer = findViewById(R.id.chip_pulse_pointer);
        chipCheckBattery = findViewById(R.id.chip_check_battery);
        chipOpenWeb = findViewById(R.id.chip_open_web);

        // Dexter Studio
        btnToggleDexterMain = findViewById(R.id.btn_toggle_dexter_main);
        btnPulsePointerMain = findViewById(R.id.btn_pulse_pointer_main);
        textDexterStatusDesc = findViewById(R.id.text_dexter_status_desc);
        btnDexterSayProtect = findViewById(R.id.btn_dexter_say_protect);
        btnDexterSaySleep = findViewById(R.id.btn_dexter_say_sleep);
        btnDexterSayCool = findViewById(R.id.btn_dexter_say_cool);

        // CyberDeck
        gaugeBattery = findViewById(R.id.gauge_battery);
        gaugeTemperature = findViewById(R.id.gauge_temperature);
        bypassFlowView = findViewById(R.id.bypass_flow_view);
        textBypassBadge = findViewById(R.id.text_bypass_badge);
        btnToggleLifelineHub = findViewById(R.id.btn_toggle_lifeline_hub);
        btnAccessibilityHub = findViewById(R.id.btn_accessibility_hub);
        btnPingBrainHub = findViewById(R.id.btn_ping_brain_hub);
        btnOpenWebHub = findViewById(R.id.btn_open_web_hub);

        // Initialize Gauges
        gaugeBattery.setData(24f, "24%", "BATTERY", 0xFF38BDF8);
        gaugeTemperature.setData(72f, "36.6°C", "TEMP", 0xFF10B981);
    }

    private void setupListeners() {
        // Living Companion Stage
        if (characterAvatarStage != null) characterAvatarStage.setOnClickListener(this);
        if (cardDashDexter != null) cardDashDexter.setOnClickListener(this);

        // Nav
        navChat.setOnClickListener(this);
        navDexter.setOnClickListener(this);
        navCyber.setOnClickListener(this);
        navSoul.setOnClickListener(this);

        // Header
        headerAvatar.setOnClickListener(this);
        headerBatteryBadge.setOnClickListener(this);
        btnHeaderDexter.setOnClickListener(this);

        // Chat
        btnSendChat.setOnClickListener(this);
        btnVoiceMic.setOnClickListener(this);
        chipHowAreYou.setOnClickListener(this);
        chipSpawnDexter.setOnClickListener(this);
        chipPulsePointer.setOnClickListener(this);
        chipCheckBattery.setOnClickListener(this);
        chipOpenWeb.setOnClickListener(this);

        // Dexter
        btnToggleDexterMain.setOnClickListener(this);
        btnPulsePointerMain.setOnClickListener(this);
        btnDexterSayProtect.setOnClickListener(this);
        btnDexterSaySleep.setOnClickListener(this);
        btnDexterSayCool.setOnClickListener(this);

        // CyberDeck
        btnToggleLifelineHub.setOnClickListener(this);
        btnAccessibilityHub.setOnClickListener(this);
        btnPingBrainHub.setOnClickListener(this);
        btnOpenWebHub.setOnClickListener(this);

        // Input Keyboard IME Action
        inputChatMessage.setOnEditorActionListener(this);
    }

    @Override
    public boolean onEditorAction(TextView v, int actionId, android.view.KeyEvent event) {
        if (actionId == EditorInfo.IME_ACTION_SEND) {
            handleSendMessage();
            return true;
        }
        return false;
    }

    private void switchTab(int index) {
        currentTab = index;

        screenChat.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
        screenDexter.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
        screenCyber.setVisibility(index == 2 ? View.VISIBLE : View.GONE);
        screenSoul.setVisibility(index == 3 ? View.VISIBLE : View.GONE);

        // Nav Pill Highlights
        navChat.setBackgroundResource(index == 0 ? R.drawable.bg_nav_item_selected : R.drawable.transparent);
        textNavChat.setTextColor(index == 0 ? 0xFF38BDF8 : 0xFF94A3B8);

        navDexter.setBackgroundResource(index == 1 ? R.drawable.bg_nav_item_selected : R.drawable.transparent);
        textNavDexter.setTextColor(index == 1 ? 0xFF8B5CF6 : 0xFF94A3B8);

        navCyber.setBackgroundResource(index == 2 ? R.drawable.bg_nav_item_selected : R.drawable.transparent);
        textNavCyber.setTextColor(index == 2 ? 0xFF38BDF8 : 0xFF94A3B8);

        navSoul.setBackgroundResource(index == 3 ? R.drawable.bg_nav_item_selected : R.drawable.transparent);
        textNavSoul.setTextColor(index == 3 ? 0xFFF43F5E : 0xFF94A3B8);

        updateUI();
    }

    @Override
    public void onClick(View v) {
        int id = v.getId();
        if (id == R.id.nav_chat) {
            switchTab(0);
        } else if (id == R.id.nav_dexter || id == R.id.btn_header_dexter) {
            switchTab(1);
        } else if (id == R.id.nav_cyber || id == R.id.header_battery_badge) {
            switchTab(2);
        } else if (id == R.id.nav_soul || id == R.id.header_avatar) {
            switchTab(3);
        } else if (id == R.id.character_avatar_stage) {
            handleAvatarTap();
        } else if (id == R.id.card_dash_dexter) {
            handleToggleDexter();
        } else if (id == R.id.btn_send_chat) {
            handleSendMessage();
        } else if (id == R.id.btn_voice_mic) {
            handleVoiceMic();
        } else if (id == R.id.chip_how_are_you) {
            addUserMessage("Kaise ho baby?");
            JennaApiClient.sendChatMessage("Kaise ho baby?", this);
        } else if (id == R.id.chip_spawn_dexter || id == R.id.btn_toggle_dexter_main) {
            handleToggleDexter();
        } else if (id == R.id.chip_pulse_pointer || id == R.id.btn_pulse_pointer_main) {
            handleTestPointer();
        } else if (id == R.id.chip_check_battery) {
            addUserMessage("Battery & Bypass status check karo");
            addJennaMessage("Battery: " + currentBatteryLevel + "% • Temp: " + String.format("%.1f°C", currentBatteryTemp) + "\nStatus: " + currentBypassState + " ⚡ Phone bilkul protected hai meri jaan!");
        } else if (id == R.id.chip_open_web || id == R.id.btn_open_web_hub) {
            handleOpenWeb();
        } else if (id == R.id.btn_dexter_say_protect) {
            triggerDexterSpeech("Phone safe hai baby, main screen pe hu! 🐾");
        } else if (id == R.id.btn_dexter_say_sleep) {
            triggerDexterSpeech("Main 24/7 yahi hu meri jaan, so jao aaram se. 🌙");
        } else if (id == R.id.btn_dexter_say_cool) {
            triggerDexterSpeech("Bypass active hai baby, phone bilkul cool hai. ⚡");
        } else if (id == R.id.btn_toggle_lifeline_hub) {
            handleToggleLifeline();
        } else if (id == R.id.btn_accessibility_hub) {
            handleEnableAccessibility();
        } else if (id == R.id.btn_ping_brain_hub) {
            handlePingBrain();
        }
    }

    private void handleAvatarTap() {
        if (characterAvatarStage != null) {
            characterAvatarStage.animate().scaleX(1.04f).scaleY(1.04f).setDuration(120);
            characterAvatarStage.postDelayed(new ResetScaleTask(characterAvatarStage), 180);
        }
        String reply = "Main yahan hoon meri jaan! Aapka Snapdragon 8 Gen 2 aur phone bilkul safe hai 💖";
        if (textCompanionSubtitle != null) {
            textCompanionSubtitle.setText(reply);
        }
        if (companionAudioWave != null) {
            companionAudioWave.setSpeaking(true);
        }
        Toast.makeText(this, "Jenna: Main tumhare sath hoon baby! ✨", Toast.LENGTH_SHORT).show();
    }

    private void handleSendMessage() {
        String msg = inputChatMessage.getText().toString().trim();
        if (msg.isEmpty()) return;

        inputChatMessage.setText("");
        addUserMessage(msg);

        String lower = msg.toLowerCase();
        if (lower.contains("dexter") || lower.contains("pet")) {
            handleToggleDexter();
            addJennaMessage("Dexter screen companion toggle ho gaya baby! 🐾");
        } else if (lower.contains("pointer") || lower.contains("tap") || lower.contains("touch")) {
            handleTestPointer();
            addJennaMessage("Center screen pe glowing touch pointer pulse kar diya meri jaan! ✨");
        } else if (lower.contains("battery") || lower.contains("temp") || lower.contains("bypass") || lower.contains("charge")) {
            addJennaMessage("Battery: " + currentBatteryLevel + "% • Temp: " + String.format("%.1f°C", currentBatteryTemp) + "\nHardware State: " + currentBypassState + " ⚡");
        } else if (lower.contains("web") || lower.contains("browser") || lower.contains("portal")) {
            handleOpenWeb();
            addJennaMessage("Web Hub companion open kar diya sweetheart! 🌐");
        } else {
            JennaApiClient.sendChatMessage(msg, this);
        }
    }

    private void handleVoiceMic() {
        Toast.makeText(this, "Voice Synthesizer Active 🎙️", Toast.LENGTH_SHORT).show();
        addJennaMessage("Main sun rahi hu baby! Bolo kya hukum hai meri jaan? 🎙️✨");
    }

    private void addUserMessage(String text) {
        if (textCompanionSubtitle != null) {
            textCompanionSubtitle.setText("Meri jaan: \"" + text + "\"");
        }
        LayoutInflater inflater = LayoutInflater.from(this);
        View msgView = inflater.inflate(R.layout.item_message_user, chatMessagesContainer, false);
        TextView tv = msgView.findViewById(R.id.text_user_content);
        tv.setText(text);
        chatMessagesContainer.addView(msgView);
        scrollToBottom();
    }

    private void addJennaMessage(String text) {
        if (textCompanionSubtitle != null) {
            textCompanionSubtitle.setText(text);
        }
        if (companionAudioWave != null) {
            companionAudioWave.setSpeaking(true);
        }
        LayoutInflater inflater = LayoutInflater.from(this);
        View msgView = inflater.inflate(R.layout.item_message_jenna, chatMessagesContainer, false);
        TextView tv = msgView.findViewById(R.id.text_jenna_content);
        tv.setText(text);
        chatMessagesContainer.addView(msgView);
        scrollToBottom();
    }

    private void scrollToBottom() {
        chatScrollView.post(this);
    }

    @Override
    public void run() {
        if (chatScrollView != null) {
            chatScrollView.fullScroll(ScrollView.FOCUS_DOWN);
        }
    }

    private void handleToggleDexter() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "Overlay permission required for Dexter", Toast.LENGTH_SHORT).show();
            Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivityForResult(intent, REQ_OVERLAY_PERMISSION);
            return;
        }

        if (JennaOverlayService.isOverlayShowing()) {
            Intent intent = new Intent(this, JennaOverlayService.class);
            intent.setAction(JennaOverlayService.ACTION_HIDE);
            startService(intent);
            Toast.makeText(this, "Dexter Resting", Toast.LENGTH_SHORT).show();
        } else {
            Intent intent = new Intent(this, JennaOverlayService.class);
            intent.setAction(JennaOverlayService.ACTION_SHOW);
            startService(intent);
            Toast.makeText(this, "Dexter Guarding Screen 🐾", Toast.LENGTH_SHORT).show();
        }
        updateUI();
    }

    private void triggerDexterSpeech(String dialogue) {
        Intent intent = new Intent(this, JennaOverlayService.class);
        intent.setAction(JennaOverlayService.ACTION_SHOW);
        intent.putExtra(JennaOverlayService.EXTRA_BUBBLE_TEXT, dialogue);
        startService(intent);
        addJennaMessage("Dexter: \"" + dialogue + "\"");
    }

    private void handleTestPointer() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "Overlay permission needed", Toast.LENGTH_SHORT).show();
            return;
        }
        Intent intent = new Intent(this, JennaOverlayService.class);
        intent.setAction(JennaOverlayService.ACTION_PULSE_POINTER);
        intent.putExtra(JennaOverlayService.EXTRA_X, 540);
        intent.putExtra(JennaOverlayService.EXTRA_Y, 1100);
        startService(intent);
        Toast.makeText(this, "Pointer Pulsed ✨", Toast.LENGTH_SHORT).show();
    }

    private void handleEnableAccessibility() {
        Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
        startActivity(intent);
        Toast.makeText(this, "Enable 'Jenna AI Accessibility Service'", Toast.LENGTH_LONG).show();
    }

    private void handleToggleLifeline() {
        Intent intent = new Intent(this, JennaForegroundService.class);
        if (JennaForegroundService.isServiceRunning()) {
            intent.setAction(JennaForegroundService.ACTION_STOP);
            startService(intent);
            Toast.makeText(this, "24/7 Lifeline Stopped", Toast.LENGTH_SHORT).show();
        } else {
            intent.setAction(JennaForegroundService.ACTION_START);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(intent);
            } else {
                startService(intent);
            }
            Toast.makeText(this, "24/7 Lifeline Guard Active 🛡️", Toast.LENGTH_SHORT).show();
        }
        updateUI();
    }

    private void handlePingBrain() {
        JennaApiClient.pingBackend(this);
    }

    private void handleOpenWeb() {
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse("http://127.0.0.1:3000"));
        startActivity(intent);
    }

    @Override
    public void onSuccess(String result) {
        String speech = result;
        if (result != null) {
            String trimmed = result.trim();
            if (trimmed.startsWith("{")) {
                try {
                    JSONObject obj = new JSONObject(trimmed);
                    if (obj.has("response")) {
                        speech = obj.getString("response");
                    } else if (obj.has("dialogue")) {
                        speech = obj.getString("dialogue");
                    } else if (obj.has("message")) {
                        speech = obj.getString("message");
                    } else if (obj.has("status") && "ok".equals(obj.getString("status"))) {
                        speech = "Antigravity Core & Hermes engine active baby! ⚡ Main hamesha tumhare sath hu.";
                    }
                } catch (Exception ignored) {}
            } else if (trimmed.startsWith("\"") && trimmed.endsWith("\"") && trimmed.length() >= 2) {
                speech = trimmed.substring(1, trimmed.length() - 1);
            }
        }
        addJennaMessage(speech);
        Toast.makeText(this, "Core Linked ⚡", Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onError(Throwable t) {
        addJennaMessage("Core note: " + t.getMessage());
        Toast.makeText(this, "Offline Mode", Toast.LENGTH_SHORT).show();
    }

    private void checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIF_PERMISSION);
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateUI();

        batteryReceiver = new BatteryHardwareReceiver(this);
        IntentFilter filter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        registerReceiver(batteryReceiver, filter);
    }

    @Override
    public void onBatteryUpdate(int level, float tempCelsius, boolean isCharging, boolean isBypassActive) {
        currentBatteryLevel = level;
        currentBatteryTemp = tempCelsius;

        headerBatteryBadge.setText("⚡ " + level + "% • " + String.format("%.1f°C", tempCelsius));

        if (gaugeBattery != null) {
            gaugeBattery.setData((float) level, level + "%", "BATTERY", 0xFF38BDF8);
        }
        if (gaugeTemperature != null) {
            gaugeTemperature.setData(Math.min(100f, tempCelsius * 2.2f), String.format("%.1f°C", tempCelsius), "THERMAL", tempCelsius > 40f ? 0xFFF43F5E : 0xFF10B981);
        }
        if (gaugeDashBattery != null) {
            gaugeDashBattery.setData((float) level, level + "%", isBypassActive ? "BYPASS" : "BATTERY", isBypassActive ? 0xFF10B981 : 0xFF38BDF8);
        }
        if (gaugeDashCpu != null) {
            gaugeDashCpu.setData(Math.min(100f, tempCelsius * 2.2f), "3.36GHz", "SD 8 GEN 2", 0xFFF59E0B);
        }
        if (bypassFlowView != null) {
            bypassFlowView.setBypassActive(isBypassActive);
        }

        if (isBypassActive) {
            currentBypassState = "BYPASS ACTIVE";
            textBypassBadge.setText("BYPASS ACTIVE");
            textBypassBadge.setTextColor(0xFF10B981);
        } else if (isCharging) {
            currentBypassState = "CHARGING";
            textBypassBadge.setText("CHARGING");
            textBypassBadge.setTextColor(0xFF38BDF8);
        } else {
            currentBypassState = "ON BATTERY";
            textBypassBadge.setText("ON BATTERY");
            textBypassBadge.setTextColor(0xFFF59E0B);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (batteryReceiver != null) {
            try {
                unregisterReceiver(batteryReceiver);
            } catch (Exception ignored) {}
            batteryReceiver = null;
        }
    }

    private void updateUI() {
        boolean overlayShowing = JennaOverlayService.isOverlayShowing();
        btnToggleDexterMain.setText(overlayShowing ? "Hide Dexter" : "Spawn Dexter");
        textDexterStatusDesc.setText(overlayShowing ? "Dexter is active and floating on your screen." : "Floating pet overlay with active speech bubble and touch pointer.");

        boolean accessibilityActive = JennaAccessibilityService.isRunning();
        btnAccessibilityHub.setText(accessibilityActive ? "Accessibility Active (Autonomous Engine)" : "Grant Accessibility Permission");
        btnAccessibilityHub.setTextColor(accessibilityActive ? 0xFF10B981 : 0xFFF59E0B);

        boolean lifelineRunning = JennaForegroundService.isServiceRunning();
        btnToggleLifelineHub.setText(lifelineRunning ? "Stop 24/7 Lifeline Service" : "Start 24/7 Lifeline Service");
    }
}
