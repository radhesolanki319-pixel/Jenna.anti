package ai.jenna.app.network;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONObject;

public class JennaApiClient {
    private static final String BASE_URL = "http://127.0.0.1:8000";
    private static final ExecutorService executor = Executors.newCachedThreadPool();

    public static void pingBackend(JennaCallback callback) {
        executor.execute(new ApiTask(BASE_URL + "/health", ApiTask.TYPE_GET, null, callback));
    }

    public static void fetchHermesDialogue(JennaCallback callback) {
        executor.execute(new ApiTask(BASE_URL + "/api/v1/antigravity/hermes/dialogue", ApiTask.TYPE_GET, null, callback));
    }

    public static void sendChatMessage(String message, JennaCallback callback) {
        JSONObject obj = new JSONObject();
        try {
            obj.put("prompt", message);
        } catch (Exception ignored) {}
        executor.execute(new ApiTask(BASE_URL + "/api/v1/antigravity/chat", ApiTask.TYPE_POST, obj.toString(), callback));
    }

    public static void postTelemetry(JSONObject data, JennaCallback callback) {
        String body = (data != null) ? data.toString() : "{}";
        executor.execute(new ApiTask(BASE_URL + "/api/v1/antigravity/telemetry", ApiTask.TYPE_POST, body, callback));
    }
}

