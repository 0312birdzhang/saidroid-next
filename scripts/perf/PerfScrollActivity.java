package org.example.saildroid.perfscroll;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Choreographer;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.widget.FrameLayout;
import android.widget.ScrollView;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Controlled frame-pump probes for the SailDroid frame-path benchmark.
 *
 * Two instruments, on purpose:
 *   - a scrolling scene (the business case; a real ScrollView + custom View drawn
 *     through the same Surface/Canvas path QQ uses), and
 *   - a pulse scene (the diagnostic case: a FrameLayout subclass that changes colour
 *     and invalidates itself every 16 ms, with no scrolling, no scrolling caches and
 *     no "nothing changed" excuses).
 *
 * PERFSCROLL_MODE (environment): heavy (default) | light | blank | touch | pulse
 * PERFSCROLL_DRIVER (environment):
 *   choreographer - View.postOnAnimation, i.e. the real Choreographer vsync path
 *                   (default); a frame only happens if a compositor frame callback
 *                   is actually delivered
 *   handler       - Handler.postDelayed(~16 ms): a timer drives the invalidations,
 *                   so it measures the pipeline even if vsync delivery is broken.
 *                   The difference between the two drivers isolates vsync delivery
 *                   from pipeline throughput.
 *   both          - both drivers; whichever produces more frames wins, and the log
 *                   says which one ran.
 *
 * The scroll content is 21600 px tall (ten 1080x2160 screens), so
 * {@code scrollTo} really changes scrollY (the first version was only 12960 px and
 * the scene never scrolled, which made "did the view redraw at all" ambiguous).
 * Every step scrolls by more than a row AND moves a marker rect, so a frame cannot
 * be skipped by "nothing changed" heuristics.
 *
 * The counters are honest: steps (driver ticks), and scrollY at every progress line.
 * Frames themselves are counted on the runtime side (SdSurfaceStore locks/unlocks/
 * draws + native presents), never inferred from these numbers.
 */
public final class PerfScrollActivity extends Activity {
    /** Tall enough that scrollY actually moves on every step. */
    private static final int CONTENT_HEIGHT = 21600;
    private static final int ROW_HEIGHT = 120;
    private static final int STEP_PIXELS = 151;

    private ScrollView scroll;
    private Content content;
    private PulseLayout pulse;
    private String mode = "heavy";
    private String driver = "choreographer";
    private boolean animate = true;
    private final Choreographer.FrameCallback appVsyncCallback = new Choreographer.FrameCallback() {
        @Override public void doFrame(long frameTimeNanos) {
            if (!animate) return;
            appVsyncs++;
            Choreographer.getInstance().postFrameCallback(this);
        }
    };
    private int steps;
    /* App-side instruments, so "did the framework even try to draw?" never depends on
       the runtime's counters: draws = root onDraw, appVsyncs = frame callbacks this app
       received from its own Choreographer. */
    private int draws;
    private int appVsyncs;
    private int choreographerSteps;
    private int handlerSteps;
    private long startedNs;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable handlerDriver = new Runnable() {
        @Override public void run() {
            if (!animate) return;
            handlerSteps++;
            step();
            handler.postDelayed(this, 16);
        }
    };
    private final Runnable choreographerDriver = new Runnable() {
        @Override public void run() {
            if (!animate) return;
            choreographerSteps++;
            step();
            driverView().postOnAnimation(this);
        }
    };

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        String requested = getIntent().getStringExtra("mode");
        if (requested == null) requested = System.getenv("PERFSCROLL_MODE");
        if (requested != null && requested.length() > 0) mode = requested;
        String requestedDriver = getIntent().getStringExtra("driver");
        if (requestedDriver == null) requestedDriver = System.getenv("PERFSCROLL_DRIVER");
        if (requestedDriver != null && requestedDriver.length() > 0) driver = requestedDriver;
        animate = !("touch".equals(mode) || "color".equals(mode));
        if ("micro".equals(mode)) {
            /* Pixel-copy microbenchmark: the frame path spends its largest single
               block in Bitmap.getPixels (34.78 ms/frame measured on QQ, r78). This
               measures the alternatives on the same device so the optimisation target
               is chosen from numbers, not from the AOSP source layout. */
            setContentView(new FrameLayout(this));
            handler.postDelayed(new Runnable() { @Override public void run() { micro(); } }, 300);
            return;
        }
        if ("color".equals(mode)) {
            /* Channel-order card: five pure bands. If the direct copy wrote RGBA
               bytes into an ARGB8888 buffer the red band would come back blue, so
               one screenshot decides the byte order instead of reasoning about it. */
            setContentView(new ColorBands(this));
        } else if ("pulse".equals(mode)) {
            pulse = new PulseLayout(this);
            setContentView(pulse);
        } else {
            content = new Content(this, mode);
            scroll = new ScrollView(this) {
                @Override protected void onScrollChanged(int x, int y, int oldX, int oldY) {
                    super.onScrollChanged(x, y, oldX, oldY);
                    if ("touch".equals(mode)) System.err.println("PERFSCROLL=touch_scroll|time_ns="
                            + System.nanoTime() + "|scrollY=" + y + "|previousY=" + oldY);
                    if (content != null) content.invalidate();
                }
                @Override public boolean dispatchTouchEvent(android.view.MotionEvent event) {
                    if ("touch".equals(mode) && event.getActionMasked() == android.view.MotionEvent.ACTION_DOWN)
                        System.err.println("PERFSCROLL=touch_down|time_ns=" + System.nanoTime()
                                + "|event_ns=" + (event.getEventTime() * 1000000L));
                    return super.dispatchTouchEvent(event);
                }
            };
            scroll.setFillViewport(false);
            scroll.setVerticalScrollBarEnabled(false);
            scroll.addView(content, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, CONTENT_HEIGHT));
            setContentView(scroll);
        }
        getWindow().addOnFrameMetricsAvailableListener(new android.view.Window.OnFrameMetricsAvailableListener(){
            @Override public void onFrameMetricsAvailable(android.view.Window window,android.view.FrameMetrics metrics,int dropped){
                System.err.println("PERFHWUI=frame|observed_ns="+System.nanoTime()
                    +"|intended_vsync_ns="+metrics.getMetric(android.view.FrameMetrics.INTENDED_VSYNC_TIMESTAMP)
                    +"|vsync_ns="+metrics.getMetric(android.view.FrameMetrics.VSYNC_TIMESTAMP)
                    +"|first_draw="+metrics.getMetric(android.view.FrameMetrics.FIRST_DRAW_FRAME)
                    +"|total_ns="+metrics.getMetric(android.view.FrameMetrics.TOTAL_DURATION)
                    +"|draw_ns="+metrics.getMetric(android.view.FrameMetrics.DRAW_DURATION)
                    +"|sync_ns="+metrics.getMetric(android.view.FrameMetrics.SYNC_DURATION)
                    +"|command_ns="+metrics.getMetric(android.view.FrameMetrics.COMMAND_ISSUE_DURATION)
                    +"|swap_ns="+metrics.getMetric(android.view.FrameMetrics.SWAP_BUFFERS_DURATION)
                    +"|dropped="+dropped+"|hardware="+window.getDecorView().isHardwareAccelerated());
            }
        },handler);
        getWindow().getDecorView().getViewTreeObserver().addOnDrawListener(
                new ViewTreeObserver.OnDrawListener() {
                    @Override public void onDraw() { draws++;if(draws==1)System.err.println("PERFSCROLL=renderer|view_hardware="+getWindow().getDecorView().isHardwareAccelerated()); }
                });
        startedNs = System.nanoTime();
        System.err.println("PERFSCROLL=created|mode=" + mode + "|driver=" + driver
                + "|content_height=" + CONTENT_HEIGHT);
    }

    @Override protected void onResume() {
        super.onResume();
        animate = !("touch".equals(mode) || "color".equals(mode) || "micro".equals(mode));
        System.err.println("PERFSCROLL=ready|mode=" + mode + "|driver=" + driver
                + "|animate=" + animate);
        if (!animate) return;
        postAppVsync();
        if ("micro".equals(mode)) return;
        if ("choreographer".equals(driver) || "both".equals(driver)) {
            driverView().postOnAnimation(choreographerDriver);
        }
        if ("handler".equals(driver) || "both".equals(driver)) {
            handler.postDelayed(handlerDriver, 16);
        }
    }

    private void postAppVsync() {
        Choreographer.getInstance().removeFrameCallback(appVsyncCallback);
        Choreographer.getInstance().postFrameCallback(appVsyncCallback);
    }

    private void micro() {
        final int w = 1080, h = 2160;
        Bitmap bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bmp);
        c.drawColor(0xff203040);
        int[] pixels = new int[w * h];
        byte[] raw = new byte[w * h * 4];
        ByteBuffer direct = ByteBuffer.allocateDirect(w * h * 4).order(ByteOrder.LITTLE_ENDIAN);
        /* warm up: one untimed pass of each, so the numbers below are steady state */
        bmp.getPixels(pixels, 0, w, 0, 0, w, h);
        System.arraycopy(raw, 0, raw, 0, raw.length);
        String err = "none";
        /* timed passes: three of each, report the median */
        double getPixelsMs = timeOf(new Runnable() { @Override public void run() {
            bmp.getPixels(pixels, 0, w, 0, 0, w, h); } }, 3);
        double arrayCopyMs = timeOf(new Runnable() { @Override public void run() {
            System.arraycopy(raw, 0, raw, 0, raw.length); } }, 3);
        double directCopyMs = -1;
        try {
            directCopyMs = timeOf(new Runnable() { @Override public void run() {
                direct.clear(); bmp.copyPixelsToBuffer(direct); } }, 3);
        } catch (Throwable t) {
            err = t.getClass().getName() + ": " + t.getMessage();
        }
        System.err.println("PERFSCROLL=micro|getpixels_ms=" + fmt(getPixelsMs)
                + "|arraycopy9mb_ms=" + fmt(arrayCopyMs)
                + "|copytobuffer_ms=" + fmt(directCopyMs)
                + "|error=" + err);
    }

    private static double timeOf(Runnable r, int passes) {
        double[] taken = new double[passes];
        for (int i = 0; i < passes; i++) {
            long t0 = System.nanoTime();
            r.run();
            taken[i] = (System.nanoTime() - t0) / 1e6;
        }
        java.util.Arrays.sort(taken);
        return taken[passes / 2];
    }

    private static String fmt(double v) { return v < 0 ? "n/a" : String.format(java.util.Locale.US, "%.2f", v); }

    /** Whichever root view owns the frame clock: the pulse probe or the scroll scene. */
    private View driverView() {
        return pulse != null ? pulse : scroll;
    }

    private void step() {
        steps++;
        if (pulse != null) {
            pulse.phase = steps;
            pulse.invalidate();
        } else if (scroll != null) {
            int viewport = Math.max(1, scroll.getHeight());
            int max = Math.max(1, CONTENT_HEIGHT - viewport);
            int next = scroll.getScrollY() + STEP_PIXELS;
            if (next > max) next = 0;
            scroll.scrollTo(0, next);
            content.phase = steps;
            content.invalidate();
        }
        if (steps % 60 == 0) {
            System.err.println("PERFSCROLL=progress|steps=" + steps
                    + "|choreographer=" + choreographerSteps
                    + "|handler=" + handlerSteps
                    + "|scrollY=" + (scroll != null ? scroll.getScrollY() : -1)
                    + "|draws=" + draws + "|appvsync=" + appVsyncs
                    + "|seconds=" + ((System.nanoTime() - startedNs) / 1e9));
        }
    }

    @Override protected void onPause() {
        animate = false;
        handler.removeCallbacks(handlerDriver);
        Choreographer.getInstance().removeFrameCallback(appVsyncCallback);
        if (driverView() != null) driverView().removeCallbacks(choreographerDriver);
        System.err.println("PERFSCROLL=paused|steps=" + steps
                + "|choreographer=" + choreographerSteps + "|handler=" + handlerSteps
                + "|scrollY=" + (scroll != null ? scroll.getScrollY() : -1)
                + "|draws=" + draws + "|appvsync=" + appVsyncs
                + "|seconds=" + ((System.nanoTime() - startedNs) / 1e9));
        super.onPause();
    }

    /** Diagnostic frame pump: no scrolling, no caches, one colour change per tick. */
    private static final class PulseLayout extends FrameLayout {
        int phase;
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        final RectF rect = new RectF();

        PulseLayout(Context context) {
            super(context);
            setBackgroundColor(0xff101820);
            setWillNotDraw(false);
        }

        @Override protected void onDraw(Canvas canvas) {
            int width = getWidth(), height = getHeight();
            int shift = (phase * 13) % Math.max(1, width - 200);
            /* int arithmetic on purpose: a long here is read as a packed ColorLong
               and ColorSpace.get() throws "Invalid ID, must be in the range [0..16)". */
            int rgb = (int) ((phase * 2654435761L) & 0xffffff);
            paint.setColor(0xff000000 | rgb);
            rect.set(shift, height / 3f, shift + 200, height / 3f + 200);
            canvas.drawRect(rect, paint);
        }

    }

    private static final class Content extends View {
        final String mode;
        int phase;
        int sceneDraws;
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
        final Paint marker = new Paint(Paint.ANTI_ALIAS_FLAG);
        final RectF rect = new RectF();

        Content(Context context, String mode) {
            super(context);
            this.mode = mode;
            text.setColor(0xffe8eef2);
            text.setTextSize(34);
            marker.setColor(0xffff8a3d);
            setBackgroundColor(0xff101820);
        }

        @Override protected void onMeasure(int widthSpec, int heightSpec) {
            /* ScrollView measures its child with an UNSPECIFIED height: the default
               View.onMeasure() would report 0, scrollTo() would clamp to 0 (the first
               version of this probe really did stay at scrollY=0), and the scene would
               never scroll at all. */
            setMeasuredDimension(resolveSize(1080, widthSpec), CONTENT_HEIGHT);
        }

        @Override protected void onDraw(Canvas canvas) {
            int width = getWidth();
            View viewport = getParent() instanceof View ? (View) getParent() : this;
            int scrollY = viewport.getScrollY();
            if ("blank".equals(mode)) {
                paint.setColor(0xff2a3f4d);
                int x = (phase * 17) % Math.max(1, width - 60);
                rect.set(x, scrollY + 40, x + 60, scrollY + 100);
                canvas.drawRect(rect, paint);
                return;
            }
            int first = Math.max(0, scrollY / ROW_HEIGHT - 1);
            int last = Math.min(CONTENT_HEIGHT / ROW_HEIGHT,
                    (scrollY + Math.max(1, viewport.getHeight()) + ROW_HEIGHT - 1) / ROW_HEIGHT + 1);
            sceneDraws++;
            if (last <= first || first * ROW_HEIGHT > scrollY
                    || last * ROW_HEIGHT < Math.min(CONTENT_HEIGHT, scrollY + viewport.getHeight()))
                throw new AssertionError("Visible scroll rows do not cover viewport");
            if (sceneDraws == 1 || sceneDraws % 120 == 0)
                System.err.println("PERFSCROLL=coverage|draw=" + sceneDraws + "|scrollY=" + scrollY
                        + "|viewport_height=" + viewport.getHeight() + "|first_row=" + first
                        + "|last_row_exclusive=" + last + "|hardware=" + canvas.isHardwareAccelerated());
            for (int row = first; row < last; row++) {
                int top = row * ROW_HEIGHT + 8;
                paint.setColor(row % 2 == 0 ? 0xff1d3342 : 0xff24404f);
                rect.set(16, top, width - 16, top + 104);
                canvas.drawRoundRect(rect, 14, 14, paint);
                if ("light".equals(mode)) continue;
                paint.setColor(0xff3f6c86);
                canvas.drawCircle(width - 70, top + 52, 30, paint);
                canvas.drawText("SailDroid row " + row, 34, top + 44, text);
                text.setColor(0xff9dbfd0);
                canvas.drawText("frame-path benchmark item " + row, 34, top + 84, text);
                text.setColor(0xffe8eef2);
            }
            /* A marker that moves on every step, so a frame is guaranteed to differ
               from the previous one even when the scroll offset repeats. */
            int markerX = (phase * 23) % Math.max(1, width - 40);
            canvas.drawRect(markerX, scrollY + 900, markerX + 40, scrollY + 940, marker);
        }
    }

    /** Pure R/G/B/W/K vertical bands: the screenshot is the colour-order oracle. */
    static final class ColorBands extends View {
        ColorBands(Context context) { super(context); }
        @Override protected void onMeasure(int wspec, int hspec) {
            setMeasuredDimension(MeasureSpec.getSize(wspec) > 0 ? MeasureSpec.getSize(wspec) : 1080,
                    MeasureSpec.getSize(hspec) > 0 ? MeasureSpec.getSize(hspec) : 2160);
        }
        @Override protected void onDraw(Canvas canvas) {
            int w = getWidth(), h = getHeight(), band = w / 5;
            Paint p = new Paint();
            p.setColor(0xFFFF0000); canvas.drawRect(0, 0, band, h, p);
            p.setColor(0xFF00FF00); canvas.drawRect(band, 0, band * 2, h, p);
            p.setColor(0xFF0000FF); canvas.drawRect(band * 2, 0, band * 3, h, p);
            p.setColor(0xFFFFFFFF); canvas.drawRect(band * 3, 0, band * 4, h, p);
            p.setColor(0xFF000000); canvas.drawRect(band * 4, 0, w, h, p);
            p.setColor(0xFFFFFFFF); p.setTextSize(60);
            canvas.drawText("R", band / 2 - 20, 120, p);
        }
    }
}
