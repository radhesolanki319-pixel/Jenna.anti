package ai.jenna.app.views;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.SweepGradient;
import android.util.AttributeSet;
import android.view.View;

public class CircularGaugeView extends View {
    private final Paint paintTrack = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintProgress = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintTextValue = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintTextLabel = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF arcRect = new RectF();

    private float progress = 75f;
    private String valueText = "75%";
    private String labelText = "POWER";
    private int accentColor = 0xFF38BDF8;

    public CircularGaugeView(Context context) {
        super(context);
        init();
    }

    public CircularGaugeView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public CircularGaugeView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        paintTrack.setStyle(Paint.Style.STROKE);
        paintTrack.setStrokeWidth(10f);
        paintTrack.setColor(0x33334155);
        paintTrack.setStrokeCap(Paint.Cap.ROUND);

        paintProgress.setStyle(Paint.Style.STROKE);
        paintProgress.setStrokeWidth(12f);
        paintProgress.setColor(accentColor);
        paintProgress.setStrokeCap(Paint.Cap.ROUND);

        paintTextValue.setColor(0xFFF8FAFC);
        paintTextValue.setTextAlign(Paint.Align.CENTER);
        paintTextValue.setFakeBoldText(true);

        paintTextLabel.setColor(0xFF94A3B8);
        paintTextLabel.setTextAlign(Paint.Align.CENTER);
    }

    public void setData(float prog, String value, String label, int color) {
        this.progress = prog;
        this.valueText = value;
        this.labelText = label;
        this.accentColor = color;
        paintProgress.setColor(color);
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        float w = getWidth();
        float h = getHeight();
        float size = Math.min(w, h);
        if (size <= 0) return;

        float stroke = size * 0.09f;
        paintTrack.setStrokeWidth(stroke);
        paintProgress.setStrokeWidth(stroke);

        float padding = stroke * 1.2f;
        arcRect.set(padding, padding, w - padding, h - padding);

        // Background Track: 270 degree arc from 135 to 405
        canvas.drawArc(arcRect, 135f, 270f, false, paintTrack);

        // Progress Arc
        float sweep = (progress / 100f) * 270f;
        canvas.drawArc(arcRect, 135f, sweep, false, paintProgress);

        // Centered Text
        float cx = w / 2f;
        float cy = h / 2f;

        paintTextValue.setTextSize(size * 0.22f);
        canvas.drawText(valueText, cx, cy + size * 0.05f, paintTextValue);

        paintTextLabel.setTextSize(size * 0.11f);
        canvas.drawText(labelText, cx, cy + size * 0.24f, paintTextLabel);
    }
}
