/* AssetProbe —— 资源层分级探针。
 * 目标：把 AssetManager / Resources 的每一步拆开，定位到底哪一步动坏堆。
 * 路径全部来自参数，同一份 dex 在 VM 和真机都能跑：
 *   args[0] = 原生库目录（含 libandroid_runtime.so 与各 *_bio.so）
 *   args[1] = libsdbridge.so 的完整路径
 *   args[2] = 要 addAssetPath 的 apk/目录
 *   args[3] = 可选的 framework-res.apk
 */
import java.io.File;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public class AssetProbe {
    static int step = 0;

    static void mark(String s) {
        step++;
        String line = "AP[" + step + "] " + s;
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

    static Object call(Object target, String name, Class<?>[] types, Object... args) throws Exception {
        Method m = target.getClass().getMethod(name, types);
        m.setAccessible(true);
        return m.invoke(target, args);
    }

    static Object callDeclared(Object target, String name, Class<?>[] types, Object... args) throws Exception {
        Method m = target.getClass().getDeclaredMethod(name, types);
        m.setAccessible(true);
        return m.invoke(target, args);
    }

    public static void main(String[] argv) {
        String libdir = argv.length > 0 ? argv[0] : "/home/art/bio2";
        String bridge = argv.length > 1 ? argv[1] : "/home/art/lib/libsdbridge.so";
        String apk    = argv.length > 2 ? argv[2] : "/home/art/realapps/systemui.apk";
        String fres   = argv.length > 3 ? argv[3] : "";

        mark("START libdir=" + libdir + " apk=" + apk);

        try {
            System.load(bridge);
            mark("bridge loaded");
        } catch (Throwable t) { fail("System.load bridge", t); return; }

        boolean ok = SdBridge.loadBionicLibrary(libdir + "/libandroid_runtime.so", libdir);
        int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
        mark("bootstrap load=" + ok + " reg=" + reg);
        if (!ok) return;

        try {
            mark("native probe: " + SdBridge.nativeAssetProbe(libdir));
        } catch (Throwable t) { fail("nativeAssetProbe", t); }

        Class<?> amc;
        try { amc = Class.forName("android.content.res.AssetManager"); }
        catch (Throwable t) { fail("forName AssetManager", t); return; }
        mark("forName AssetManager ok");

        Constructor<?> ctor;
        try { ctor = amc.getDeclaredConstructor(); ctor.setAccessible(true); }
        catch (Throwable t) { fail("get AssetManager()", t); return; }
        mark("ctor handle ok");

        Object am;
        try { am = ctor.newInstance(); }
        catch (Throwable t) { fail("new AssetManager", t); return; }
        mark("new AssetManager = " + am);

        if (!fres.isEmpty()) {
            try {
                Object c2 = call(am, "addAssetPath", new Class<?>[]{ String.class }, fres);
                mark("addAssetPath(framework-res) cookie=" + c2);
            } catch (Throwable t) { fail("addAssetPath framework-res", t); }
        }

        try {
            Object cookie = call(am, "addAssetPath", new Class<?>[]{ String.class }, apk);
            mark("addAssetPath(" + apk + ") cookie=" + cookie);
        } catch (Throwable t) { fail("addAssetPath app apk", t); }

        Class<?> resc;
        try { resc = Class.forName("android.content.res.Resources"); }
        catch (Throwable t) { fail("forName Resources", t); return; }
        mark("forName Resources ok");

        Object res = null;
        try {
            Constructor<?> rc = resc.getConstructor(amc, Class.forName("android.util.DisplayMetrics"),
                                                   Class.forName("android.content.res.Configuration"));
            rc.setAccessible(true);
            res = rc.newInstance(am, null, null);
            mark("new Resources = " + res);
        } catch (Throwable t) { fail("new Resources", t); }

        if (res != null) {
            try {
                Object dm = call(res, "getDisplayMetrics", new Class<?>[]{});
                mark("getDisplayMetrics = " + dm);
            } catch (Throwable t) { fail("getDisplayMetrics", t); }
            try {
                Object id = callDeclared(res, "getIdentifier",
                        new Class<?>[]{ String.class, String.class, String.class },
                        "app_name", "string", "android");
                mark("getIdentifier(app_name) = " + id);
            } catch (Throwable t) { fail("getIdentifier", t); }
            try {
                Object cs = call(res, "getStringArray", new Class<?>[]{
                        Class.forName("android.content.res.Resources$Theme") }, (Object) null);
                mark("unexpected getStringArray = " + cs);
            } catch (Throwable t) {
                mark("getStringArray probe: " + t.getClass().getName() + " (expected)");
            }
        }

        mark("DONE");
    }
}
