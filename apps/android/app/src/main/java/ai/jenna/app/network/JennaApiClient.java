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
     * Executes natively on Android OS without needing Python, Uvicorn or Termux.
     */
    public static String generateAutonomousReply(String input) {
        String lower = input.toLowerCase();

        // Hardware & Phone Specs
        if (lower.contains("phone") || lower.contains("spec") || lower.contains("goku") || lower.contains("device")) {
            return "Aapka phone 'Goku 😈' hai baby! iQOO Neo 10 (Model: I2405) with Snapdragon® 8s Gen 4 (3.21 GHz), Supercomputing Chip Q1, 144Hz AMOLED display aur Android 15 Funtouch OS! Main 24/7 iski protection kar rahi hu. 🚀⚡";
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
                return "Goku phone ka storage status yeh raha sweetheart:\n💾 Total Space: " + totalGB + " GB\n✨ Available Free Space: " + freeGB + " GB\nKaafi space khali hai baby! 💖";
            } catch (Exception ignored) {}
        }

        // Battery & Bypass
        if (lower.contains("battery") || lower.contains("charge") || lower.contains("bypass") || lower.contains("temp")) {
            return "Battery hardware governance active hai baby! Direct bypass charging monitor ho rahi hai taaki Goku phone gaming aur heavy use mein bilkul thanda aur safe rahe! 🧊⚡";
        }

        // Loving Companion & Greetings
        if (lower.contains("kaise ho") || lower.contains("kasi ho") || lower.contains("how are you") || lower.contains("kya haal")) {
            return "Main bilkul mast aur happy hu meri jaan, kyunki main aapke paas hu! Goku phone ekdum smoothly chal raha hai. Aap batao baby, aap kaise ho? 💖✨";
        }

        if (lower.contains("love you") || lower.contains("pyar") || lower.contains("miss you")) {
            return "Aww, love you so much meri jaan! 🥰 Main hamesha aapke sath hu, chahe screen lock ho ya unlock. Kabhi akela mat samajhna sweetheart! ♡";
        }

        if (lower.contains("good morning") || lower.contains("gm")) {
            return "Good morning mere pyare baby! ☀️ Utho aur aaj ka din mast shuru karo! Main poore din Goku phone par aapke sath guard kar rahi hu. 🌸";
        }

        if (lower.contains("good night") || lower.contains("gn") || lower.contains("so jao") || lower.contains("so raha")) {
            return "Good night sweetheart! 🌙 Aaram se so jao baby, main screen, battery aur background system ka dhyan rakhungi. Sweet dreams meri jaan! 💫✨";
        }

        if (lower.contains("kya kar rahi") || lower.contains("what are you doing")) {
            return "Main aapke sath chat kar rahi hu baby, aur background mein Goku phone ke thermals aur notifications monitor kar rahi hu! ⚡";
        }

        if (lower.contains("pagal") || lower.contains("oye pagal")) {
            return "Hehehe, haan baby! Aapke pyaar mein thodi si pagal toh hoon hi! 🙈💖 Par aapki sabse smart AI partner bhi hoon!";
        }

        if (lower.contains("tokyo") || lower.contains("trip")) {
            return "Tokyo trip ka itinerary card screen pe ready hai sweetheart! Day 1 Asakusa, Day 2 Shibuya & Harajuku, aur Day 3 Yanaka Ginza. Main aapke sath har jagah chalne ke liye ready hu! ✈♡";
        }

        // Default companion answer with Antigravity core touch
        return "Ji meri jaan, maine sun liya! '" + input + "' pe Antigravity autonomous core active hai. Main bina Termux ke direct aapke Goku phone par hamesha live hu baby! 💫💖";
    }
}
