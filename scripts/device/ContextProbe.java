/* ContextProbe —— Context / ActivityThread 分级探针。
 * 资源层已经通了，接下来要拿到一个能用的 Context，才能走 Application/Activity 生命周期。
 * 每一步都打标记，失败就打印最内层原因和栈。
 *
 * 参数：
 *   args[0] = 原生库目录（含 libandroid_runtime.so）
 *   args[1] = libsdbridge.so 完整路径
 *   args[2] = framework-res.apk（可选，用于 addAssetPath）
 */
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

public class ContextProbe {
    static int step = 0;

    static void mark(String s) {
        step++;
        String line = "CP[" + step + "] " + s;
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
        for (int i = 0; i < st.length && i < 10; i++) System.err.println("    at " + st[i]);
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
        String apk    = argv.length > 2 ? argv[2] : "";

        // --- 引导 ---
        try {
            System.load(bridge);
            boolean ok = SdBridge.loadBionicLibrary(libdir + "/libandroid_runtime.so", libdir);
            int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
            mark("bootstrap load=" + ok + " reg=" + reg);
            if (!ok) return;
        } catch (Throwable t) { fail("bootstrap", t); return; }

        Class<?> atc;
        try { atc = Class.forName("android.app.ActivityThread"); }
        catch (Throwable t) { fail("forName ActivityThread", t); return; }
        mark("ActivityThread 类可见");

        // --- A0: 主线程 Looper。真实进程里 ActivityThread.main() 先做这一步，
        //         我们不经过 main()，就得自己准备，否则 Handler 构造会抛
        //         "Can't create handler inside thread that has not called Looper.prepare()" ---
        mark("A0: Looper.prepareMainLooper()");
        try {
            Class<?> looper = Class.forName("android.os.Looper");
            staticCall(looper, "prepareMainLooper", new Class<?>[]{});
            Object main = staticCall(looper, "myLooper", new Class<?>[]{});
            mark("A0 ok: myLooper = " + main);
        } catch (Throwable t) { fail("prepareMainLooper", t); }

        // --- A: ActivityThread.systemMain() ---
        Object at = null;
        mark("A: ActivityThread.systemMain()");
        try { at = staticCall(atc, "systemMain", new Class<?>[]{}); mark("A ok: " + at); }
        catch (Throwable t) { fail("systemMain", t); }

        if (at == null) {
            // 退化路径：直接 new ActivityThread()，不走 attach
            mark("A2: new ActivityThread()");
            try {
                Constructor<?> c = atc.getDeclaredConstructor();
                c.setAccessible(true);
                at = c.newInstance();
                mark("A2 ok: " + at);
            } catch (Throwable t) { fail("new ActivityThread", t); }
        }
        if (at == null) { mark("DONE(没有 ActivityThread)"); return; }

        // --- B: ContextImpl.createSystemContext(ActivityThread) ---
        mark("B: ContextImpl.createSystemContext()");
        Object ctx = null;
        Class<?> cic;
        try { cic = Class.forName("android.app.ContextImpl"); }
        catch (Throwable t) { fail("forName ContextImpl", t); return; }
        try {
            ctx = staticCall(cic, "createSystemContext", new Class<?>[]{ atc }, at);
            mark("B ok: " + ctx);
        } catch (Throwable t) { fail("createSystemContext", t); }

        if (ctx == null) {
            mark("B2: createAppContext()");
            try {
                Class<?> lac = Class.forName("android.app.LoadedApk");
                Constructor<?> lc = lac.getDeclaredConstructor(atc, ClassLoader.class);
                lc.setAccessible(true);
                Object loaded = lc.newInstance(at, null);
                ctx = staticCall(cic, "createAppContext", new Class<?>[]{ atc, lac }, at, loaded);
                mark("B2 ok: " + ctx);
            } catch (Throwable t) { fail("createAppContext", t); }
        }
        if (ctx == null) { mark("DONE(没有 Context)"); return; }

        // --- C: 依次取资源、包名、各种目录 ---
        try { mark("C resources = " + call(ctx, "getResources", new Class<?>[]{})); }
        catch (Throwable t) { fail("getResources", t); }

        try { mark("D packageName = " + call(ctx, "getPackageName", new Class<?>[]{})); }
        catch (Throwable t) { fail("getPackageName", t); }

        try {
            Object dir = call(ctx, "getFilesDir", new Class<?>[]{});
            mark("E filesDir = " + dir);
        } catch (Throwable t) { fail("getFilesDir", t); }

        try {
            Object dir = call(ctx, "getCacheDir", new Class<?>[]{});
            mark("F cacheDir = " + dir);
        } catch (Throwable t) { fail("getCacheDir", t); }

        try {
            Object pkg = call(ctx, "getPackageManager", new Class<?>[]{});
            mark("G packageManager = " + pkg);
        } catch (Throwable t) { fail("getPackageManager", t); }

        String[] services = { "window", "activity", "layout_inflater", "asset", "display" };
        for (String s : services) {
            try {
                Object svc = call(ctx, "getSystemService", new Class<?>[]{ String.class }, s);
                mark("H getSystemService(" + s + ") = " + svc);
            } catch (Throwable t) { fail("getSystemService(" + s + ")", t); }
        }

        // --- I: 用 Context 的 Resources 真正解一个资源 ---
        try {
            Object res = call(ctx, "getResources", new Class<?>[]{});
            Object dm = call(res, "getDisplayMetrics", new Class<?>[]{});
            mark("I displayMetrics = " + dm);
            Object str = call(res, "getString", new Class<?>[]{ int.class }, 0x01040000);
            mark("I getString(0x01040000) = " + str);
        } catch (Throwable t) { fail("Resources 解资源", t); }

        mark("DONE");
    }
}
