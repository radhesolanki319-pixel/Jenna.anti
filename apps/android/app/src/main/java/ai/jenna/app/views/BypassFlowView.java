package ai.jenna.app.views;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.View;

public class BypassFlowView extends View {
    private final Paint paintLine = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintPulse = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintNode = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintText = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF nodeRect = new RectF();

    private boolean isBypassActive = true;
    private float pulsePhase = 0f;

    public BypassFlowView(Context context) {
        super(context);
        init();
    }

    public BypassFlowView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public BypassFlowView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        paintLine.setStyle(Paint.Style.STROKE);
        paintLine.setStrokeWidth(4f);
        paintLine.setColor(0x4038BDF8);

        paintPulse.setStyle(Paint.Style.FILL);
        paintPulse.setColor(0xFF00F0FF);

        paintNode.setStyle(Paint.Style.FILL);

        paintText.setTextAlign(Paint.Align.CENTER);
        paintText.setFakeBoldText(true);
    }

    public void setBypassActive(boolean active) {
        this.isBypassActive = active;
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        float w = getWidth();
        float h = getHeight();
        if (w <= 0 || h <= 0) return;

        pulsePhase = (pulsePhase + 0.05f) % 1.0f;

        float cy = h * 0.38f;
        float xCharger = w * 0.16f;
        float xSwitch = w * 0.50f;
        float xCpu = w * 0.84f;
        float yBat = h * 0.82f;

        // 1. Draw Direct Power Rail (Charger -> Switch -> CPU)
        paintLine.setColor(isBypassActive ? 0xFF10B981 : 0x4038BDF8);
        canvas.drawLine(xCharger, cy, xSwitch, cy, paintLine);
        canvas.drawLine(xSwitch, cy, xCpu, cy, paintLine);

        // 2. Draw Battery Rail (Switch -> Battery)
        paintLine.setColor(isBypassActive ? 0x2264748B : 0xFF38BDF8);
        canvas.drawLine(xSwitch, cy, xSwitch, yBat, paintLine);

        // 3. Moving Energy Particle
        if (isBypassActive) {
            float particleX = xCharger + (xCpu - xCharger) * pulsePhase;
            paintPulse.setColor(0xFF10B981);
            canvas.drawCircle(particleX, cy, 7f, paintPulse);
        } else {
            float particlePhase2 = pulsePhase * 2f;
            if (particlePhase2 < 1.0f) {
                float px = xCharger + (xSwitch - xCharger) * particlePhase2;
                canvas.drawCircle(px, cy, 6f, paintPulse);
            } else {
                float py = cy + (yBat - cy) * (particlePhase2 - 1.0f);
                canvas.drawCircle(xSwitch, py, 6f, paintPulse);
            }
        }

        // 4. Draw Nodes
        drawNode(canvas, xCharger, cy, 32f, 22f, "POWER IN", 0xFF1E293B, 0xFF38BDF8);
        drawNode(canvas, xSwitch, cy, 36f, 24f, isBypassActive ? "BYPASS" : "CHARGING", isBypassActive ? 0xFF064E3B : 0xFF1E293B, isBypassActive ? 0xFF34D399 : 0xFF38BDF8);
        drawNode(canvas, xCpu, cy, 34f, 22f, "SNAPDRAGON", 0xFF1E293B, 0xFF8B5CF6);
        drawNode(canvas, xSwitch, yBat, 34f, 22f, isBypassActive ? "BAT: RESTING" : "BAT: CHARGING", isBypassActive ? 0xFF0F172A : 0xFF1E293B, isBypassActive ? 0xFF64748B : 0xFFF59E0B);

        postInvalidateOnAnimation();
    }

    private void drawNode(Canvas canvas, float cx, float cy, float hw, float hh, String label, int bgCol, int textCol) {
        nodeRect.set(cx - hw, cy - hh, cx + hw, cy + hh);
        paintNode.setColor(bgCol);
        canvas.drawRoundRect(nodeRect, 10f, 10f, paintNode);

        paintText.setColor(textCol);
        paintText.setTextSize(hh * 0.7f);
        canvas.drawText(label, cx, cy + hh * 0.35f, paintText);
    }
}
