/* LiveProbe —— 真手指的交互闭环。
 *
 * 数据流：
 *   sdview --evfile /home/art/events.txt --watch /home/art/live.rgba
 *     ↓ 手指在窗口上按/拖/抬，sdview 往 events.txt 追加 "D x y" / "M x y" / "U"
 *   LiveProbe 轮询 events.txt，转成 MotionEvent 交给 View 树
 *     ↓ View 状态改变后重画到 Bitmap，写回 live.rgba
 *   sdview --watch 发现 live.rgba 变了，重新贴到 Wayland 窗口
 * 结果就是手指点一下，屏幕跟着变。
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
import java.io.RandomAccessFile;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class LiveProbe {
    static int step = 0;
    static final int W = 540;
    static final int H = 1080;

    static void mark(String s) {
        step++;
        String line = "LP[" + step + "] " + s;
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
        String evPath = argv.length > 2 ? argv[2] : "/home/art/events.txt";
        String outPath = argv.length > 3 ? argv[3] : "/home/art/live.rgba";
        int seconds = argv.length > 4 ? Integer.parseInt(argv[4]) : 120;

        try {
            System.load(bridge);
            boolean ok = SdBridge.loadBionicLibrary(libdir + "/libandroid_runtime.so", libdir);
            int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
            mark("bootstrap load=" + ok + " reg=" + reg);
            if (!ok) return;
            mark("服务安装: " + SdServices.installAll());
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
        root.addView(pad, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1.0f));
        root.measure(View.MeasureSpec.makeMeasureSpec(W, View.MeasureSpec.EXACTLY),
                     View.MeasureSpec.makeMeasureSpec(H, View.MeasureSpec.EXACTLY));
        root.layout(0, 0, W, H);
        mark("View 树就绪 " + root.getMeasuredWidth() + "x" + root.getMeasuredHeight());

        // 先写一帧空闲态，让 sdview 有东西可显示
        renderAndWrite(root, outPath);
        mark("首帧已写出 " + outPath);

        RandomAccessFile ev = null;
        try {
            ev = new RandomAccessFile(evPath, "r");
            ev.seek(ev.length());        // 只处理启动之后的事件
            mark("监听事件文件 " + evPath);
        } catch (Throwable t) { fail("打开事件文件", t); return; }

        long deadline = System.currentTimeMillis() + seconds * 1000L;
        long lastRender = 0;
        int events = 0;
        String partial = "";
        int dirty = 0;

        mark("进入事件循环 " + seconds + " 秒");
        long hbLast = System.currentTimeMillis();
        try {
            while (System.currentTimeMillis() < deadline) {
                long len = ev.length();
                long pos = ev.getFilePointer();
                if (len > pos) {
                    int n = (int) (len - pos);
                    byte[] buf = new byte[n];
                    ev.readFully(buf);
                    // 不走 new String(byte[],"UTF-8")：避免依赖 charset 解码链，
                    // 这里的事件全是 ASCII，直接按字节拼字符。
                    char[] cs = new char[n];
                    for (int i = 0; i < n; i++) cs[i] = (char) (buf[i] & 0xff);
                    String text = partial + new String(cs);
                    int nl;
                    while ((nl = text.indexOf('\n')) >= 0) {
                        String line = text.substring(0, nl).trim();
                        text = text.substring(nl + 1);
                        if (line.isEmpty()) continue;
                        if (dispatchLine(root, pad, line)) { events++; dirty++; }
                    }
                    partial = text;
                } else {
                    Thread.sleep(12);
                }
                long now = System.currentTimeMillis();
                if (dirty > 0 && now - lastRender > 25) {
                    renderAndWrite(root, outPath);
                    lastRender = now;
                    dirty = 0;
                }
                if (now - hbLast >= 2000) {
                    hbLast = now;
                    mark("心跳 len=" + ev.length() + " pos=" + ev.getFilePointer()
                            + " events=" + events);
                }
            }
        } catch (Throwable t) { fail("事件循环", t); }

        mark("事件总数=" + events);
        mark("TouchPad 记录:\n" + pad.dump());
        mark("DONE");
    }

    static boolean dispatchLine(View root, TouchPad pad, String line) {
        try {
            char kind = line.charAt(0);
            long now = System.currentTimeMillis();
            if (kind == 'D' || kind == 'M') {
                String[] p = line.split("\\s+");
                float x = Float.parseFloat(p[1]);
                float y = Float.parseFloat(p[2]);
                int action = kind == 'D' ? MotionEvent.ACTION_DOWN : MotionEvent.ACTION_MOVE;
                if (kind == 'D') pad.downTime = now;
                MotionEvent e = MotionEvent.obtain(pad.downTime, now, action, x, y, 0);
                boolean r = root.dispatchTouchEvent(e);
                e.recycle();
                pad.note(kind, x, y, r);
                return true;
            }
            if (kind == 'U') {
                float x = pad.lastX, y = pad.lastY;
                MotionEvent e = MotionEvent.obtain(pad.downTime, now, MotionEvent.ACTION_UP, x, y, 0);
                boolean r = root.dispatchTouchEvent(e);
                e.recycle();
                pad.note('U', x, y, r);
                return true;
            }
            if (kind == 'C') {
                MotionEvent e = MotionEvent.obtain(pad.downTime, now, MotionEvent.ACTION_CANCEL,
                        pad.lastX, pad.lastY, 0);
                root.dispatchTouchEvent(e);
                e.recycle();
                pad.note('C', pad.lastX, pad.lastY, true);
                return true;
            }
        } catch (Throwable t) { fail("dispatchLine(" + line + ")", t); }
        return false;
    }

    static void renderAndWrite(View root, String path) {
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
        } catch (Throwable t) { fail("renderAndWrite", t); }
    }

    public static class TouchPad extends View {
        private final StringBuilder log = new StringBuilder();
        int state = 0;
        float lastX = W / 2f, lastY = H / 2f;
        long downTime = 0;

        public TouchPad(Context c) {
            super(c);
            setClickable(true);
        }

        void note(char kind, float x, float y, boolean handled) {
            if (log.length() < 4000) {
                log.append(kind).append(' ').append((int) x).append(',').append((int) y)
                   .append(handled ? " ok" : " no").append('\n');
            }
        }

        @Override
        public boolean onTouchEvent(MotionEvent e) {
            int a = e.getActionMasked();
            switch (a) {
                case MotionEvent.ACTION_DOWN:
                    state = 1; lastX = e.getX(); lastY = e.getY(); break;
                case MotionEvent.ACTION_MOVE:
                    state = 2; lastX = e.getX(); lastY = e.getY(); break;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    state = 3; break;
                default:
                    return super.onTouchEvent(e);
            }
            invalidate();
            return true;
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            Paint p = new Paint();
            int c;
            switch (state) {
                case 1:  c = 0xFF4CC38A; break;
                case 2:  c = 0xFF51A0E0; break;
                case 3:  c = 0xFFE05252; break;
                default: c = 0xFF2A3947; break;
            }
            p.setColor(c);
            canvas.drawRect(0, 0, getWidth(), getHeight(), p);
            if (state >= 1) {
                p.setColor(0xFFFFFFFF);
                canvas.drawCircle(lastX, lastY, 60, p);
                p.setColor(0x66000000);
                canvas.drawCircle(lastX, lastY, 100, p);
            }
        }

        String dump() {
            return log.toString();
        }
    }
}
