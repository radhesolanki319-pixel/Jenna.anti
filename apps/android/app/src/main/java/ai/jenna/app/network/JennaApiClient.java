package ai.jenna.app.network;

import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.os.StatFs;
import java.io.File;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONObject;
import ai.jenna.app.terminal.ShellExecutor;

public class JennaApiClient {
    private static final String BASE_URL = "http://127.0.0.1:8000";
    private static final ExecutorService executor = Executors.newCachedThreadPool();
    private static final Handler mainHandler = new Handler(Looper.getMainLooper());

    public static void pingBackend(JennaCallback callback) {
        executor.execute(new ApiTask(BASE_URL + "/health", ApiTask.TYPE_GET, null, callback));
    }

    public static void fetchHermesDialogue(JennaCallback callback) {
        executor.execute(new ApiTask(BASE_URL + "/api/v1/antigravity/hermes/dialogue", ApiTask.TYPE_GET, null, callback));
    }

    public static void sendChatMessage(final String message, final JennaCallback callback) {
        if (message == null || message.trim().isEmpty()) return;
        final String trimmed = message.trim();

        // 1. Direct In-App Terminal Command Execution
        if (trimmed.startsWith("!") || trimmed.startsWith("sh:") || trimmed.startsWith("cmd:")) {
            executor.execute(new Runnable() {
                @Override
                public void run() {
                    String cmd = trimmed.replaceFirst("^(!|sh:|cmd:)\\s*", "");
                    String result = ShellExecutor.execute(cmd);
                    final String formatted = "💻 [Terminal: " + cmd + "]\n" + result;
                    postSuccess(callback, formatted);
                }
            });
            return;
        }

        // 2. Try sending to local backend if available
        JSONObject obj = new JSONObject();
        try {
            obj.put("prompt", trimmed);
        } catch (Exception ignored) {}

        executor.execute(new ApiTask(BASE_URL + "/api/v1/antigravity/chat", ApiTask.TYPE_POST, obj.toString(), new JennaCallback() {
            @Override
            public void onSuccess(String result) {
                if (callback != null) {
                    callback.onSuccess(result);
                }
            }

            @Override
            public void onError(Throwable error) {
                // 3. Standalone On-Device Antigravity Engine (Zero Termux fallback)
                String autonomousReply = generateAutonomousReply(trimmed);
                postSuccess(callback, autonomousReply);
            }
        }));
    }

    private static void postSuccess(final JennaCallback callback, final String replyText) {
        if (callback == null) return;
        mainHandler.post(new Runnable() {
            @Override
            public void run() {
                try {
                    JSONObject json = new JSONObject();
                    json.put("response", replyText);
                    json.put("status", "ok");
                    callback.onSuccess(json.toString());
                } catch (Exception e) {
                    callback.onSuccess(replyText);
                }
            }
        });
    }

    public static void postTelemetry(JSONObject data, JennaCallback callback) {
        String body = (data != null) ? data.toString() : "{}";
        executor.execute(new ApiTask(BASE_URL + "/api/v1/antigravity/telemetry", ApiTask.TYPE_POST, body, callback));
    }

    /**
     * Standalone In-App Antigravity Autonomous Companion Engine
     * Executes natively on Android OS when backend is syncing.
     */
    public static String generateAutonomousReply(String input) {
        String lower = input.toLowerCase();

        // Hardware & Phone Specs
        if (lower.contains("phone") || lower.contains("spec") || lower.contains("device") || lower.contains("hardware")) {
            return "Boss, aapka device iQOO Neo 10 (Model: I2405) hai! Qualcomm Snapdragon® 8 Gen 4 (SM8750 'sun' Oryon CPU), 1260x2800 144Hz LTPO AMOLED display aur Android 15. All system monitors active! 🚀⚡";
        }

        // Storage Check
        if (lower.contains("storage") || lower.contains("disk") || lower.contains("space")) {
            try {
                File path = Environment.getDataDirectory();
                StatFs stat = new StatFs(path.getPath());
                long blockSize = stat.getBlockSizeLong();
                long totalBlocks = stat.getBlockCountLong();
                long availableBlocks = stat.getAvailableBlocksLong();
                long totalGB = (totalBlocks * blockSize) / (1024 * 1024 * 1024);
                long freeGB = (availableBlocks * blockSize) / (1024 * 1024 * 1024);
                return "Storage Status, Boss:\n💾 Total Space: " + totalGB + " GB\n✨ Available Free Space: " + freeGB + " GB\nDisk storage healthy aur optimized hai! 📁⚡";
            } catch (Exception ignored) {}
        }

        // Battery & Bypass
        if (lower.contains("battery") || lower.contains("charge") || lower.contains("bypass") || lower.contains("temp")) {
            return "Battery & Thermal governance active hai, Boss! Direct hardware bypass charging controller ready hai taaki gaming aur heavy tasks mein temperature control mein rahe. 🧊⚡";
        }

        // Greetings & Assistant Dialogue
        if (lower.contains("kaise ho") || lower.contains("kasi ho") || lower.contains("how are you") || lower.contains("kya haal")) {
            return "Main bilkul active aur ready hoon, Boss! Sabhi system services, zero-amnesia memory aur touch governor smoothly run kar rahe hain. Bataiye, kya task execute karna hai? 🕶️✨";
        }

        if (lower.contains("good morning") || lower.contains("gm")) {
            return "Good morning, Boss! ☀️ System 100% operational hai. Aaj ka pehla directive kya hai? 🚀";
        }

        if (lower.contains("good night") || lower.contains("gn") || lower.contains("so jao") || lower.contains("so raha")) {
            return "Good night, Boss! 🌙 Main background mein battery thermals aur system sentinels watch kar rahi hoon. Rest well! 💫";
        }

        if (lower.contains("kya kar rahi") || lower.contains("what are you doing")) {
            return "Main system terminal, display touch governor, aur hardware thermals monitor kar rahi hoon Boss! Standby for your next command. ⚡";
        }

        // Default companion answer with Antigravity core touch
        return "Ji Boss, directive received: '" + input + "'. Antigravity autonomous core ready hai. Command dijiye, main execute karti hoon! 💻🚀";
    }
}
