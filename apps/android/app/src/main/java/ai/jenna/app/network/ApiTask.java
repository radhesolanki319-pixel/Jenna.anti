package ai.jenna.app.network;

import android.os.Handler;
import android.os.Looper;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class ApiTask implements Runnable {
    public static final int TYPE_GET = 1;
    public static final int TYPE_POST = 2;

    private static final Handler mainHandler = new Handler(Looper.getMainLooper());

    private final String urlString;
    private final int requestType;
    private final String postData;
    private final JennaCallback callback;

    public ApiTask(String urlString, int requestType, String postData, JennaCallback callback) {
        this.urlString = urlString;
        this.requestType = requestType;
        this.postData = postData;
        this.callback = callback;
    }

    @Override
    public void run() {
        try {
            URL url = new URL(urlString);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(3000);
            conn.setReadTimeout(3000);

            if (requestType == TYPE_POST) {
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json; utf-8");
                conn.setDoOutput(true);
                if (postData != null) {
                    byte[] input = postData.getBytes(StandardCharsets.UTF_8);
                    try (OutputStream os = conn.getOutputStream()) {
                        os.write(input, 0, input.length);
                    }
                }
            } else {
                conn.setRequestMethod("GET");
            }

            int code = conn.getResponseCode();
            if (code >= 200 && code < 300) {
                BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = in.readLine()) != null) {
                    sb.append(line);
                }
                in.close();
                postResult(sb.toString(), null);
            } else {
                postResult(null, new Exception("HTTP error code: " + code));
            }
        } catch (Exception e) {
            postResult(null, e);
        }
    }

    private void postResult(final String result, final Throwable error) {
        if (callback == null) return;
        mainHandler.post(new ResultDispatcher(callback, result, error));
    }
}
