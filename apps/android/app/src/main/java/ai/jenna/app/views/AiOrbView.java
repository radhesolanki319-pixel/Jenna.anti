package ai.jenna.app.views;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.RectF;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.view.View;

public class AiOrbView extends View {
    private final Paint paintGlow = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintRing1 = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintRing2 = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintCore = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintSpark = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF oval1 = new RectF();
    private final RectF oval2 = new RectF();

    private float phase = 0f;
    private boolean isBreathing = true;

    public AiOrbView(Context context) {
        super(context);
        init();
    }

    public AiOrbView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public AiOrbView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        paintRing1.setStyle(Paint.Style.STROKE);
        paintRing1.setStrokeWidth(3.5f);
        paintRing1.setColor(0xFF38BDF8); // Cyber cyan

        paintRing2.setStyle(Paint.Style.STROKE);
        paintRing2.setStrokeWidth(2.5f);
        paintRing2.setColor(0xFFF43F5E); // Neon Rose

        paintSpark.setStyle(Paint.Style.FILL);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        float cx = getWidth() / 2f;
        float cy = getHeight() / 2f;
        float baseRadius = Math.min(cx, cy) * 0.55f;
        if (baseRadius <= 0) return;

        phase += 0.04f;
        if (phase > 2000000f) phase = 0f;

        // Dynamic breathing scale (sine oscillation between 0.95 and 1.05)
        float breath = 1.0f + 0.08f * (float) Math.sin(phase);
        float radius = baseRadius * breath;

        // 1. Outer Ambient Radial Glow
        int glowColorInner = 0x55F43F5E; // 33% Neon rose
        int glowColorOuter = 0x000F172A; // Transparent
        RadialGradient glowShader = new RadialGradient(
                cx, cy, radius * 1.6f,
                glowColorInner, glowColorOuter,
                Shader.TileMode.CLAMP
        );
        paintGlow.setShader(glowShader);
        canvas.drawCircle(cx, cy, radius * 1.6f, paintGlow);

        // 2. Rotating Concentric Outer Neon Arc Rings
        float ring1Radius = radius * 1.25f;
        oval1.set(cx - ring1Radius, cy - ring1Radius, cx + ring1Radius, cy + ring1Radius);
        float angle1 = (phase * 45f) % 360f;
        canvas.drawArc(oval1, angle1, 100, false, paintRing1);
        canvas.drawArc(oval1, angle1 + 180f, 100, false, paintRing1);

        float ring2Radius = radius * 1.42f;
        oval2.set(cx - ring2Radius, cy - ring2Radius, cx + ring2Radius, cy + ring2Radius);
        float angle2 = (-phase * 30f) % 360f;
        canvas.drawArc(oval2, angle2, 70, false, paintRing2);
        canvas.drawArc(oval2, angle2 + 120f, 70, false, paintRing2);
        canvas.drawArc(oval2, angle2 + 240f, 70, false, paintRing2);

        // 3. Central Core Glowing Orb with Cyber Gradient
        RadialGradient coreShader = new RadialGradient(
                cx - radius * 0.2f, cy - radius * 0.25f, radius,
                new int[]{0xFFFFFFFF, 0xFF38BDF8, 0xFF8B5CF6, 0xFFF43F5E},
                new float[]{0.0f, 0.35f, 0.75f, 1.0f},
                Shader.TileMode.CLAMP
        );
        paintCore.setShader(coreShader);
        canvas.drawCircle(cx, cy, radius, paintCore);

        // 4. Orbiting Sparks
        for (int i = 0; i < 4; i++) {
            float sparkAngle = (phase * 1.5f + (float) (i * Math.PI / 2.0));
            float sparkDist = radius * (1.1f + 0.18f * (float) Math.sin(phase * 2f + i));
            float sx = cx + sparkDist * (float) Math.cos(sparkAngle);
            float sy = cy + sparkDist * (float) Math.sin(sparkAngle);
            paintSpark.setColor((i % 2 == 0) ? 0xFF00F0FF : 0xFFFF2E93);
            canvas.drawCircle(sx, sy, 4.5f + (float) Math.sin(phase + i) * 1.5f, paintSpark);
        }

        if (isBreathing) {
            postInvalidateOnAnimation();
        }
    }
}
