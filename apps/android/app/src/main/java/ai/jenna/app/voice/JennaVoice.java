package ai.jenna.app.voice;

import android.content.Context;
import android.speech.tts.TextToSpeech;
import java.util.Locale;

public class JennaVoice implements TextToSpeech.OnInitListener {
    private static JennaVoice instance;
    private TextToSpeech tts;
    private boolean isReady = false;

    public static synchronized JennaVoice getInstance(Context context) {
        if (instance == null) {
            instance = new JennaVoice(context.getApplicationContext());
        }
        return instance;
    }

    private JennaVoice(Context context) {
        tts = new TextToSpeech(context, this);
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            int result = tts.setLanguage(new Locale("hi", "IN"));
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                tts.setLanguage(Locale.US);
            }
            tts.setPitch(1.22f); // Sweet companion pitch
            tts.setSpeechRate(1.02f);
            isReady = true;
        }
    }

    public void speak(String text) {
        if (tts != null && isReady && text != null && !text.isEmpty()) {
            // Clean markdown markers or emojis for smooth speech
            String cleaned = text.replaceAll("[*#_`~>▶▼✈♡👋🏛🏢⛰]", "").trim();
            tts.speak(cleaned, TextToSpeech.QUEUE_FLUSH, null, "jenna_voice_" + System.currentTimeMillis());
        }
    }

    public void stop() {
        if (tts != null) {
            tts.stop();
        }
    }

    public void shutdown() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
            instance = null;
        }
    }
}
