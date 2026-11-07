/* ViewProbe —— 真实 Android View 树的 measure / layout / draw 到 Bitmap。
 *
 * 输出文件格式与 sdview 对齐：
 *   "SDRGBA\0" + uint32 w(LE) + uint32 h(LE) + w*h 个 uint32(ARGB, LE)
 * Android 的 ARGB_8888 在内存里就是 BGRA 字节序，所以 copyPixelsToBuffer 直接可用。
 *
 * 注意：这一版刻意不画文字。Skia 画字形需要字体文件（/system/etc/fonts.xml 那套），
 * 当前部署里还没有，先把 measure/layout/draw 这条链走通，文字单独处理。
 */
import java.io.FileOutputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class ViewProbe {
    static int step = 0;
    static final int W = 540;
    static final int H = 1080;

    static void mark(String s) {
        step++;
        String line = "VP[" + step + "] " + s;
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

    static Object call(Object target, String name, Class<?>[] types, Object... args) throws Exception {
        Method m = target.getClass().getMethod(name, types);
        m.setAccessible(true);
        return m.invoke(target, args);
    }

    public static void main(String[] argv) {
        String libdir = argv.length > 0 ? argv[0] : "/home/art/bio2";
        String bridge = argv.length > 1 ? argv[1] : "/home/art/lib/libsdbridge.so";
        String out    = argv.length > 2 ? argv[2] : "/home/art/view.rgba";

        try {
            System.load(bridge);
            boolean ok = SdBridge.loadBionicLibrary(libdir + "/libandroid_runtime.so", libdir);
            int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
            mark("bootstrap load=" + ok + " reg=" + reg);
            if (!ok) return;
        } catch (Throwable t) { fail("bootstrap", t); return; }

        Object ctx = null;
        try {
            mark("装本地 Display: " + SdDisplayShim.install());
            mark("装本地 WindowManager: " + SdDisplayShim.installWindowManager());
        } catch (Throwable t) { fail("SdDisplayShim.install", t); return; }

        try {
            Class<?> looper = Class.forName("android.os.Looper");
            staticCall(looper, "prepareMainLooper", new Class<?>[]{});
            Class<?> atc = Class.forName("android.app.ActivityThread");
            Object at = staticCall(atc, "systemMain", new Class<?>[]{});
            mark("ActivityThread.systemMain 成功");
            Class<?> cic = Class.forName("android.app.ContextImpl");
            ctx = staticCall(cic, "createSystemContext", new Class<?>[]{ atc }, at);
            mark("Context = " + ctx);
        } catch (Throwable t) { fail("准备 Context", t); return; }

        Class<?> viewC, vgC, llC, canvasC, bmpC, paintC;
        try {
            viewC   = Class.forName("android.view.View");
            vgC     = Class.forName("android.view.ViewGroup");
            llC     = Class.forName("android.widget.LinearLayout");
            canvasC = Class.forName("android.graphics.Canvas");
            bmpC    = Class.forName("android.graphics.Bitmap");
            paintC  = Class.forName("android.graphics.Paint");
            mark("View/ViewGroup/LinearLayout/Bitmap/Canvas/Paint 类都可见");
        } catch (Throwable t) { fail("加载 View 类", t); return; }

        // --- 建一棵真实 View 树 ---
        Object root = null, a = null, b = null, c3 = null;
        try {
            Constructor<?> llk = llC.getConstructor(Class.forName("android.content.Context"));
            llk.setAccessible(true);
            root = llk.newInstance(ctx);
            Method setOrient = llC.getMethod("setOrientation", int.class);
            setOrient.invoke(root, 1);           // VERTICAL
            call(root, "setBackgroundColor", new Class<?>[]{ int.class }, 0xFF0E1621);

            Constructor<?> vk = Bar.class.getConstructor(Class.forName("android.content.Context"), int.class);
            vk.setAccessible(true);
            a = vk.newInstance(ctx, 0xFFE05252);
            b = vk.newInstance(ctx, 0xFF4CC38A);
            c3 = vk.newInstance(ctx, 0xFF51A0E0);
            /* 给每个子 View 一个 LayoutParams(MATCH_PARENT, 0, weight=1)，
             * 否则默认 WRAP_CONTENT 会被量成 0 高，三个条子只剩第一条能看见。 */
            Class<?> lpc = Class.forName("android.view.ViewGroup$LayoutParams");
            Class<?> llpc = Class.forName("android.widget.LinearLayout$LayoutParams");
            Constructor<?> lpctor = llpc.getConstructor(int.class, int.class, float.class);
            lpctor.setAccessible(true);
            int MATCH_PARENT = -1;
            Method addViewLp = vgC.getMethod("addView", viewC, lpc);
            for (Object v : new Object[]{ a, b, c3 }) {
                Object lp = lpctor.newInstance(MATCH_PARENT, 0, 1.0f);
                addViewLp.invoke(root, v, lp);
            }
            mark("View 树建好: LinearLayout + 3 个自绘 View");
        } catch (Throwable t) { fail("建 View 树", t); return; }

        // --- measure / layout ---
        try {
            Class<?> ms = Class.forName("android.view.View$MeasureSpec");
            Method makeSpec = ms.getMethod("makeMeasureSpec", int.class, int.class);
            int EXACTLY = 0x40000000;
            int wSpec = (Integer) makeSpec.invoke(null, W, EXACTLY);
            int hSpec = (Integer) makeSpec.invoke(null, H, EXACTLY);
            call(root, "measure", new Class<?>[]{ int.class, int.class }, wSpec, hSpec);
            mark("measure 完成: " + call(root, "getMeasuredWidth", new Class<?>[]{})
                    + "x" + call(root, "getMeasuredHeight", new Class<?>[]{}));
            call(root, "layout", new Class<?>[]{ int.class, int.class, int.class, int.class },
                    0, 0, W, H);
            mark("layout 完成: " + call(root, "getWidth", new Class<?>[]{})
                    + "x" + call(root, "getHeight", new Class<?>[]{}));
        } catch (Throwable t) { fail("measure/layout", t); return; }

        // --- 画到 Bitmap ---
        Object bmp = null;
        try {
            Method create = bmpC.getMethod("createBitmap", int.class, int.class,
                    Class.forName("android.graphics.Bitmap$Config"));
            Object cfg = Enum.valueOf((Class<Enum>) Class.forName("android.graphics.Bitmap$Config"),
                                      "ARGB_8888");
            bmp = create.invoke(null, W, H, cfg);
            mark("Bitmap = " + bmp + " rowBytes=" + call(bmp, "getRowBytes", new Class<?>[]{}));

            Constructor<?> ck = canvasC.getConstructor(bmpC);
            Object canvas = ck.newInstance(bmp);
            call(root, "draw", new Class<?>[]{ canvasC }, canvas);
            mark("View.draw 完成");
        } catch (Throwable t) { fail("draw", t); return; }

        // --- 写文件 ---
        // 不用 Bitmap.copyPixelsToBuffer：这条 native 路径在本环境下会
        // "free(): invalid pointer" 崩掉（已记录，后面单独查）。
        // 改用公开的 getPixels(int[]) 取整幅，再手工按 BGRA 字节序写盘。
        try {
            int[] pixels = new int[W * H];
            mark("写文件: 取整幅像素 " + W + "x" + H);
            Method getPixels = bmpC.getMethod("getPixels", int[].class, int.class, int.class,
                    int.class, int.class, int.class, int.class);
            getPixels.invoke(bmp, pixels, 0, W, 0, 0, W, H);
            mark("写文件: getPixels 完成");

            FileOutputStream fos = new FileOutputStream(out);
            fos.write(new byte[]{ 'S', 'D', 'R', 'G', 'B', 'A', 0 });
            ByteBuffer hdr = ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN);
            hdr.putInt(W); hdr.putInt(H);
            fos.write(hdr.array());

            byte[] chunk = new byte[8192];
            int ci = 0;
            for (int i = 0; i < pixels.length; i++) {
                int p = pixels[i];
                chunk[ci++] = (byte) (p & 0xFF);           // B
                chunk[ci++] = (byte) ((p >> 8) & 0xFF);    // G
                chunk[ci++] = (byte) ((p >> 16) & 0xFF);   // R
                chunk[ci++] = (byte) ((p >> 24) & 0xFF);   // A
                if (ci == chunk.length) {
                    fos.write(chunk, 0, ci);
                    ci = 0;
                }
            }
            if (ci > 0) fos.write(chunk, 0, ci);
            fos.close();
            mark("写文件: 已落盘 " + out);
        } catch (Throwable t) { fail("写文件", t); }

        // --- 取像素判断有没有真的画上去 ---
        try {
            int[] px = new int[1];
            Method getPixels = bmpC.getMethod("getPixels", int[].class, int.class, int.class,
                    int.class, int.class, int.class, int.class);
            getPixels.invoke(bmp, px, 0, 0, W / 2, H / 2, 1, 1);
            mark(String.format("中心像素 = %08x", px[0]));
            getPixels.invoke(bmp, px, 0, 0, W / 2, H / 4, 1, 1);
            mark(String.format("上 1/4 像素 = %08x", px[0]));
        } catch (Throwable t) { fail("读像素", t); }

        // --- 带主题的控件探测：放在最后，崩了也不丢画面 ---
        for (String n : new String[]{ "android.widget.TextView", "android.widget.Button" }) {
            mark("准备构造控件: " + n);
            try {
                Class<?> c = Class.forName(n);
                Constructor<?> k = c.getConstructor(Class.forName("android.content.Context"));
                k.setAccessible(true);
                Object o = k.newInstance((Object) ctx);
                mark("控件可构造: " + n + " -> " + o);
            } catch (Throwable t) {
                Throwable c2 = t; while (c2.getCause() != null) c2 = c2.getCause();
                mark("控件构造失败: " + n + " : " + c2.getClass().getSimpleName() + ": " + c2.getMessage());
            }
        }

        mark("DONE");
    }

    /** 自绘 View：只用 Canvas + Paint 画几何色块，不依赖主题和字体 */
    public static class Bar extends android.view.View {
        private final int color;

        public Bar(android.content.Context c, int color) {
            super(c);
            this.color = color;
        }

        @Override
        protected void onDraw(android.graphics.Canvas canvas) {
            super.onDraw(canvas);
            int w = getWidth(), h = getHeight();
            android.graphics.Paint p = new android.graphics.Paint();
            p.setColor(color);
            canvas.drawRect(0, 0, w, h * 0.72f, p);
            p.setColor(0xFF7A8CA6);
            canvas.drawRect(0, h * 0.72f, w * 0.55f, h * 0.86f, p);
            p.setColor(0xFF2A3947);
            canvas.drawRect(w * 0.6f, h * 0.72f, w, h * 0.86f, p);
        }
    }
}
