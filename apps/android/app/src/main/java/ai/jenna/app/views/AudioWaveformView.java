package ai.jenna.app.views;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.view.View;

public class AudioWaveformView extends View {
    private final Paint paintWave = new Paint(Paint.ANTI_ALIAS_FLAG);
    private boolean isSpeaking = true;
    private float phase = 0f;

    public AudioWaveformView(Context context) {
        super(context);
        init();
    }

    public AudioWaveformView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public AudioWaveformView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        paintWave.setStyle(Paint.Style.STROKE);
        paintWave.setStrokeCap(Paint.Cap.ROUND);
        paintWave.setStrokeWidth(4f);
    }

    public void setSpeaking(boolean speaking) {
        this.isSpeaking = speaking;
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        float w = getWidth();
        float h = getHeight();
        if (w <= 0 || h <= 0) return;

        float midY = h / 2f;
        int barCount = 36;
        float spacing = w / (float) barCount;
        float barWidth = spacing * 0.45f;
        paintWave.setStrokeWidth(barWidth);

        LinearGradient gradient = new LinearGradient(
                0, 0, w, 0,
                new int[]{0xFF38BDF8, 0xFFF43F5E, 0xFF38BDF8},
                null,
                Shader.TileMode.CLAMP
        );
        paintWave.setShader(gradient);

        phase += 0.08f;
        if (phase > 1000f) phase = 0f;

        for (int i = 0; i < barCount; i++) {
            float x = i * spacing + spacing / 2f;
            // Calculate a wave amplitude with sinusoidal modulation
            float normalizedX = (float) i / (float) barCount;
            // Bell envelope so edges taper down
            float envelope = (float) Math.sin(normalizedX * Math.PI);

            float wave1 = (float) Math.sin(phase * 2.5f + i * 0.4f);
            float wave2 = (float) Math.cos(phase * 1.8f - i * 0.3f);
            float combined = (wave1 + wave2) * 0.5f;

            float maxAmp = (h / 2f - 4f) * (isSpeaking ? 0.95f : 0.35f);
            float currentAmp = Math.max(3f, Math.abs(combined) * maxAmp * envelope);

            canvas.drawLine(x, midY - currentAmp, x, midY + currentAmp, paintWave);
        }

        // 30 FPS continuous smooth animation without any lambdas
        postInvalidateDelayed(33);
    }
}
