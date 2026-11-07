/* TouchProbe —— 触摸闭环：合成 MotionEvent -> dispatchTouchEvent -> View 状态改变 -> 重新渲染。
 *
 * 输出两帧：
 *   /home/art/touch-down.rgba  DOWN 之后（按下态）
 *   /home/art/touch-up.rgba    UP   之后（抬起态）
 * 如果两帧颜色不同，说明事件真的穿透到 View 并改动了绘制结果。
 *
 * 帧格式与 sdview 一致： "SDRGBA\0" + uint32 w(LE) + uint32 h(LE) + w*h ARGB(LE)
 */
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;

import java.io.FileOutputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class TouchProbe {
    static int step = 0;
    static final int W = 540;
    static final int H = 1080;

    static void mark(String s) {
        step++;
        String line = "TP[" + step + "] " + s;
        System.err.println(line);
        System.err.flush();
        System.out.println(line);
        System.out.flush();
    }

    static void fail(String s, Throwable t) {
        Throwable c = t;
        while (c.getCause() != null) c = c.getCause();
        mark("FAIL " + s + " : " + c.getClass().getName() + ": " + c.getMessage());
        StackTraceElement[] st = c.getStackTrace();
        for (int i = 0; i < st.length && i < 8; i++) System.err.println("    at " + st[i]);
        System.err.flush();
    }

    static Object staticCall(Class<?> c, String name, Class<?>[] types, Object... args) throws Exception {
        Method m = c.getDeclaredMethod(name, types);
        m.setAccessible(true);
        return m.invoke(null, args);
    }

    public static void main(String[] argv) {
        String libdir = argv.length > 0 ? argv[0] : "/home/art/bio2";
        String bridge = argv.length > 1 ? argv[1] : "/home/art/lib/libsdbridge.so";
        String prefix = argv.length > 2 ? argv[2] : "/home/art/touch";

        try {
            System.load(bridge);
            boolean ok = SdBridge.loadBionicLibrary(libdir + "/libandroid_runtime.so", libdir);
            int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
            mark("bootstrap load=" + ok + " reg=" + reg);
            if (!ok) return;
            mark("Display: " + SdDisplayShim.install());
            mark("WindowManager: " + SdDisplayShim.installWindowManager());
        } catch (Throwable t) { fail("bootstrap", t); return; }

        Context ctx;
        try {
            Class<?> looper = Class.forName("android.os.Looper");
            staticCall(looper, "prepareMainLooper", new Class<?>[]{});
            Class<?> atc = Class.forName("android.app.ActivityThread");
            Object at = staticCall(atc, "systemMain", new Class<?>[]{});
            Class<?> cic = Class.forName("android.app.ContextImpl");
            ctx = (Context) staticCall(cic, "createSystemContext", new Class<?>[]{ atc }, at);
            mark("Context = " + ctx);
        } catch (Throwable t) { fail("准备 Context", t); return; }

        LinearLayout root = new LinearLayout(ctx);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0E1621);

        TouchPad pad = new TouchPad(ctx);
        LinearLayout.LayoutParams lp =
                new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1.0f);
        root.addView(pad, lp);
        mark("View 树建好: LinearLayout + TouchPad");

        root.measure(View.MeasureSpec.makeMeasureSpec(W, View.MeasureSpec.EXACTLY),
                     View.MeasureSpec.makeMeasureSpec(H, View.MeasureSpec.EXACTLY));
        root.layout(0, 0, W, H);
        mark("measure/layout = " + root.getMeasuredWidth() + "x" + root.getMeasuredHeight()
                + " pad=" + pad.getWidth() + "x" + pad.getHeight());

        // --- DOWN ---
        long t0 = 1000;
        MotionEvent down = MotionEvent.obtain(t0, t0, MotionEvent.ACTION_DOWN, W / 2f, H / 2f, 0);
        boolean handledDown = root.dispatchTouchEvent(down);
        mark("dispatchTouchEvent(DOWN) handled=" + handledDown);
        down.recycle();

        // --- MOVE ---
        MotionEvent move = MotionEvent.obtain(t0, t0 + 50, MotionEvent.ACTION_MOVE,
                W / 2f + 100, H / 2f + 150, 0);
        boolean handledMove = root.dispatchTouchEvent(move);
        mark("dispatchTouchEvent(MOVE) handled=" + handledMove);
        move.recycle();

        renderAndWrite(root, ctx, prefix + "-down.rgba");

        // --- UP ---
        MotionEvent up = MotionEvent.obtain(t0, t0 + 120, MotionEvent.ACTION_UP,
                W / 2f + 100, H / 2f + 150, 0);
        boolean handledUp = root.dispatchTouchEvent(up);
        mark("dispatchTouchEvent(UP) handled=" + handledUp);
        up.recycle();

        renderAndWrite(root, ctx, prefix + "-up.rgba");

        mark("TouchPad 收到的事件:\n" + pad.dump());
        mark("DONE");
    }

    static void renderAndWrite(View root, Context ctx, String path) {
        try {
            Bitmap bmp = Bitmap.createBitmap(W, H, Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(bmp);
            root.draw(canvas);

            int[] pixels = new int[W * H];
            bmp.getPixels(pixels, 0, W, 0, 0, W, H);

            FileOutputStream fos = new FileOutputStream(path);
            fos.write(new byte[]{ 'S', 'D', 'R', 'G', 'B', 'A', 0 });
            ByteBuffer hdr = ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN);
            hdr.putInt(W); hdr.putInt(H);
            fos.write(hdr.array());

            byte[] chunk = new byte[8192];
            int ci = 0;
            for (int i = 0; i < pixels.length; i++) {
                int p = pixels[i];
                chunk[ci++] = (byte) (p & 0xFF);
                chunk[ci++] = (byte) ((p >> 8) & 0xFF);
                chunk[ci++] = (byte) ((p >> 16) & 0xFF);
                chunk[ci++] = (byte) ((p >> 24) & 0xFF);
                if (ci == chunk.length) { fos.write(chunk, 0, ci); ci = 0; }
            }
            if (ci > 0) fos.write(chunk, 0, ci);
            fos.close();
            mark("已写出 " + path + "  中心像素=" + Integer.toHexString(pixels[(H / 2) * W + W / 2]));
        } catch (Throwable t) { fail("渲染/写文件 " + path, t); }
    }

    /** 记录触摸并改变自己画什么，用来证明事件真的到达了 View */
    public static class TouchPad extends View {
        private final StringBuilder log = new StringBuilder();
        private int state = 0;          // 0 idle / 1 down / 2 move / 3 up
        private float lastX, lastY;

        public TouchPad(Context c) {
            super(c);
            setClickable(true);
        }

        @Override
        public boolean onTouchEvent(MotionEvent e) {
            int a = e.getActionMasked();
            log.append("action=").append(a)
               .append(" x=").append(e.getX())
               .append(" y=").append(e.getY())
               .append(" -> ");
            boolean r;
            switch (a) {
                case MotionEvent.ACTION_DOWN:
                    state = 1; lastX = e.getX(); lastY = e.getY(); r = true; break;
                case MotionEvent.ACTION_MOVE:
                    state = 2; lastX = e.getX(); lastY = e.getY(); r = true; break;
                case MotionEvent.ACTION_UP:
                    state = 3; r = true; break;
                default:
                    r = super.onTouchEvent(e); break;
            }
            log.append(r).append('\n');
            invalidate();
            return r;
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            Paint p = new Paint();
            int c;
            switch (state) {
                case 1:  c = 0xFF4CC38A; break;   // 按下：绿
                case 2:  c = 0xFF51A0E0; break;   // 拖动：蓝
                case 3:  c = 0xFFE05252; break;   // 抬起：红
                default: c = 0xFF2A3947; break;   // 空闲：深灰
            }
            p.setColor(c);
            canvas.drawRect(0, 0, getWidth(), getHeight(), p);
            if (state >= 1) {
                p.setColor(0xFFFFFFFF);
                canvas.drawCircle(lastX, lastY, 70, p);
            }
        }

        String dump() {
            return log.toString();
        }
    }
}
