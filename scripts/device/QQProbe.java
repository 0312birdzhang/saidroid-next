/* QQProbe —— 把 QQ 的 dex 和资源接进当前运行时。
 *
 * 分步验证，每步单独打标记：
 *   1. 用 AssetManager.addAssetPath 打开 QQ 的 APK，读出它自己的资源
 *   2. 用 LoadedApk 的唯一应用类加载器加载 QQ（40 个 dex，约 390 MB）
 *   3. 确认关键类可见：QFixApplicationImplProxy / SplashActivity
 *   4. 用 QQ 的 Resources 解一个它自己的字符串资源
 *
 * 参数：
 *   args[0] 原生库目录      args[1] libsdbridge.so
 *   args[2] QQ apk 路径     args[3] QQ native lib 目录（可选）
 */
import android.content.res.AssetManager;
import android.content.res.Resources;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

public class QQProbe {
    static int step = 0;
    static final String PACKAGE = "com.tencent.mobileqq";
    static final String ODEX_DIR = "/home/art/data/qq/odex";

    static void mark(String s) {
        step++;
        String line = "QP[" + step + "] " + s;
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
        for (int i = 0; i < st.length && i < 16; i++) System.err.println("    at " + st[i]);
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
        String qqApk  = argv.length > 2 ? argv[2] : "/home/art/realapps/qq.apk";
        String qqLibs = argv.length > 3 ? argv[3] : "/home/art/realapps/qq-libs";
        final String activityApk = qqApk;
        final boolean launchActivity = argv.length > 5 && "activity".equals(argv[5]);

        try {
            System.load(bridge);
            boolean ok = SdBridge.loadBionicLibrary(libdir + "/libandroid_runtime.so", libdir);
            int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
            mark("bootstrap load=" + ok + " reg=" + reg);
            if (!ok) return;
            mark("服务安装: " + SdServices.installAll());
        } catch (Throwable t) { fail("bootstrap", t); return; }

        Object ctx = null;
        try {
            Class<?> looper = Class.forName("android.os.Looper");
            staticCall(looper, "prepareMainLooper", new Class<?>[]{});
            Class<?> atc = Class.forName("android.app.ActivityThread");
            Object at = staticCall(atc, "systemMain", new Class<?>[]{});
            SdActivityHost.applyDisplayConfiguration((android.app.ActivityThread) at);
            Class<?> cic = Class.forName("android.app.ContextImpl");
            ctx = staticCall(cic, "createSystemContext", new Class<?>[]{ atc }, at);
            mark("Context = " + ctx);
        } catch (Throwable t) { fail("准备 Context", t); return; }

        // --- 0. PackageManager 自检 ---
        try {
            Object pm = ctx.getClass().getMethod("getPackageManager").invoke(ctx);
            mark("getPackageManager() = " + pm);
            if (pm != null) {
                Class<?> pmc = Class.forName("android.content.pm.PackageManager");
                Object pi = pmc.getMethod("getPackageInfo",
                        String.class, int.class).invoke(pm, "com.tencent.mobileqq", 0);
                mark("getPackageInfo(qq) = " + pi);
                Object ai = pmc.getMethod("getApplicationInfo",
                        String.class, int.class).invoke(pm, "com.tencent.mobileqq", 0);
                mark("getApplicationInfo(qq) = " + ai);
                Class<?> aiCls = ai.getClass();
                mark("  sourceDir=" + aiCls.getField("sourceDir").get(ai)
                        + " nativeLibraryDir=" + aiCls.getField("nativeLibraryDir").get(ai)
                        + " dataDir=" + aiCls.getField("dataDir").get(ai)
                        + " uid=" + aiCls.getField("uid").get(ai));
            }
        } catch (Throwable t) { fail("PackageManager 自检", t); }

        // --- 1. QQ 的资源 ---
        Resources qqRes = null;
        try {
            AssetManager am = AssetManager.class.getConstructor().newInstance();
            int cookie = (Integer) am.getClass().getMethod("addAssetPath", String.class)
                    .invoke(am, qqApk);
            mark("AssetManager.addAssetPath(qq.apk) cookie=" + cookie);
            if (cookie == 0) { mark("QQ APK 打不开，后面没意义"); return; }
            Constructor<Resources> rc = Resources.class.getConstructor(
                    AssetManager.class,
                    Class.forName("android.util.DisplayMetrics"),
                    Class.forName("android.content.res.Configuration"));
            qqRes = rc.newInstance(am, null, null);
            mark("QQ Resources = " + qqRes);
            Object dm = qqRes.getDisplayMetrics();
            mark("QQ DisplayMetrics = " + dm);
        } catch (Throwable t) { fail("QQ 资源", t); }

        if (qqRes != null) {
            try {
                int id = qqRes.getIdentifier("app_name", "string", "com.tencent.mobileqq");
                mark("getIdentifier(app_name, com.tencent.mobileqq) = 0x" + Integer.toHexString(id));
                if (id != 0) mark("QQ 自己的字符串 = " + qqRes.getString(id));
                int pkgId = qqRes.getIdentifier("app_name", "string", "com.tencent.mobileqq");
                mark("包名资源解析 ok=" + (pkgId != 0));
            } catch (Throwable t) { fail("读 QQ 字符串资源", t); }
        }

        /* 注意：这里不要再拿自己的 DexClassLoader 去 Runtime.loadLibrary("mmkv")。
         * ART 的库表是按路径记的，一旦被某个 ClassLoader 先加载，换成 App 的 PathClassLoader
         * 就会报 "already opened by ClassLoader ..." 而拒绝。natives 是按 Class 对象注册的，
         * 所以只能由 App 的类加载器来加载。 */

        // --- 3.5 让 ActivityThread 创建 QQ 的 Application ---
        // 这一步才真正进 QQ 自己的代码：LoadedApk 会按 sourceDir 建类加载器，
        // newApplication 反射实例化 QQ 的 Application 类，然后 attach + onCreate。
        try {
            Object pm = ctx.getClass().getMethod("getPackageManager").invoke(ctx);
            Class<?> pmc = Class.forName("android.content.pm.PackageManager");
            Object ai = pmc.getMethod("getApplicationInfo", String.class, int.class)
                    .invoke(pm, PACKAGE, 0);
            mark("QQ ApplicationInfo = " + ai);
            SdServices.bindApplication((android.content.pm.ApplicationInfo) ai);

            Class<?> atc2 = Class.forName("android.app.ActivityThread");
            Object at2 = atc2.getMethod("currentActivityThread").invoke(null);
            mark("currentActivityThread = " + at2);

            Class<?> aiCls = Class.forName("android.content.pm.ApplicationInfo");
            Class<?> compatCls = Class.forName("android.content.res.CompatibilityInfo");
            Method gpn = atc2.getMethod("getPackageInfoNoCheck", aiCls, compatCls);
            Object loadedApk = gpn.invoke(at2, ai, null);
            mark("LoadedApk = " + loadedApk);

            /* systemMain() initially binds the framework's system application.
             * Supply the real hosted application's bind data before its attach
             * code asks ActivityThread.currentPackageName/currentProcessName. */
            Class<?> bindClass = Class.forName("android.app.ActivityThread$AppBindData");
            Constructor<?> bindConstructor = bindClass.getDeclaredConstructor();
            bindConstructor.setAccessible(true);
            Object bindData = bindConstructor.newInstance();
            String[] bindFields = {"appInfo", "info", "processName", "compatInfo"};
            Object[] bindValues = {ai, loadedApk,
                    ((android.content.pm.ApplicationInfo) ai).processName,
                    android.content.res.CompatibilityInfo.DEFAULT_COMPATIBILITY_INFO};
            for (int i = 0; i < bindFields.length; i++) {
                java.lang.reflect.Field field = bindClass.getDeclaredField(bindFields[i]);
                field.setAccessible(true);
                field.set(bindData, bindValues[i]);
            }
            java.lang.reflect.Field bound = atc2.getDeclaredField("mBoundApplication");
            bound.setAccessible(true);
            bound.set(at2, bindData);

            /* natives 是按 Class 对象注册的。QQ 自己的启动任务用 LoadedApk 的类加载器加载类，
             * 所以必须用同一个加载器预载 native 库，注册到的才是 QQ 实际看到的那个 Class。 */
            ClassLoader appCl = (ClassLoader) loadedApk.getClass()
                    .getMethod("getClassLoader").invoke(loadedApk);
            mark("App ClassLoader = " + appCl);
            Class<?> applicationClass = Class.forName(
                    ((android.content.pm.ApplicationInfo) ai).className, false, appCl);
            ClassLoader nativeOwner = applicationClass.getClassLoader();
            if (nativeOwner == null) {
                throw new IllegalStateException("APK Application unexpectedly belongs to boot loader");
            }
            mark("Application defining loader = " + nativeOwner);
            /* Do not open all 40 dex files through a diagnostic DexClassLoader
             * first. Validate the required classes through the same loader that
             * will own the Application and its native registrations. */
            String[] requiredClasses = {
                    "com.tencent.common.app.QFixApplicationImplProxy",
                    "com.tencent.mobileqq.activity.SplashActivity",
                    "com.tencent.mobileqq.app.BaseActivity"
            };
            for (String name : requiredClasses) {
                Class<?> type = Class.forName(name, false, appCl);
                mark("类可见: " + name + " loader=" + type.getClassLoader());
            }
            /* 把 QQ 的 native 库目录注册进 bionic 搜索路径，否则绝对路径会报 not found */
            mark("注册 bionic 库路径: " + SdBridge.addBionicLibraryPath(qqLibs));

            Class<?> rt2 = Class.forName("java.lang.Runtime");
            Object rtInst = rt2.getMethod("getRuntime").invoke(null);
            Method loadLib = rt2.getMethod("loadLibrary", String.class, ClassLoader.class);
            /* 先让这个加载器真正加载一个类：ART 的 ClassLoader.allocator 是在
             * ClassLinker::CreateClassLoader 里设置的，刚 new 出来还没用过时可能是空的，
             * 而 LoadNativeLibrary 里有 CHECK(class_loader_allocator != nullptr)。 */
            try {
                Class<?> warm = Class.forName("com.tencent.mmkv.MMKV", false, appCl);
                mark("预热类加载: " + warm);
            } catch (Throwable te) {
                mark("预热类加载失败: " + te);
            }
            String[] preloads = { "mmkv" };
            for (String lib : preloads) {
                try {
                    loadLib.invoke(rtInst, lib, nativeOwner);
                    mark("预载 lib" + lib + " (App 类加载器) 成功");
                } catch (Throwable te) {
                    Throwable c3 = te; while (c3.getCause() != null) c3 = c3.getCause();
                    mark("预载 lib" + lib + " 失败: " + c3.getClass().getSimpleName() + ": " + c3.getMessage());
                }
            }

            Class<?> lac = Class.forName("android.app.LoadedApk");
            Method makeApp = lac.getMethod("makeApplication", boolean.class,
                    Class.forName("android.app.Instrumentation"));
            Object app = makeApp.invoke(loadedApk, Boolean.FALSE, null);
            mark("QQ Application = " + app);
            if (app != null) {
                mark("   Application class = " + app.getClass().getName());
                Object base = app.getClass().getMethod("getBaseContext").invoke(app);
                mark("   baseContext = " + base);
                java.lang.reflect.Field initial = atc2.getDeclaredField("mInitialApplication");
                initial.setAccessible(true);
                initial.set(at2, app);
                if (android.app.ActivityThread.currentApplication() != app
                        || !PACKAGE.equals(android.app.ActivityThread.currentPackageName())
                        || !((android.content.pm.ApplicationInfo) ai).processName.equals(
                                android.app.ActivityThread.currentProcessName())) {
                    throw new IllegalStateException("ActivityThread application binding mismatch");
                }
                mark("ActivityThread application/package/process binding verified");
                /* makeApplication(false, null) creates and attaches Application,
                 * but its null Instrumentation branch does not call onCreate.
                 * Match ActivityThread's separate application-start step. */
                android.app.Instrumentation instrumentation = new android.app.Instrumentation();
                instrumentation.callApplicationOnCreate((android.app.Application) app);
                mark("QQ Application.onCreate completed");
            }
        } catch (Throwable t) {
            fail("创建 QQ Application", t);
            // A failed probe owns no live app session. SDK worker threads must
            // not turn a caught startup failure into a misleading exit0/hang.
            Runtime.getRuntime().halt(10);
            return;
        }

        // --- 4. 用 QQ 的布局验证布局解析 ---
        try {
            int lid = qqRes.getIdentifier("main_tab", "layout", "com.tencent.mobileqq");
            mark("getIdentifier(main_tab, layout) = 0x" + Integer.toHexString(lid));
            if (lid == 0) {
                mark("layout name main_tab absent; resource IDs must come from the APK");
            } else {
                mark("getLayout = " + qqRes.getLayout(lid));
            }
        } catch (Throwable t) { fail("QQ 布局", t); }

        // SDK callbacks queued during Application startup belong on the real
        // Android main Looper. A bounded initialization check ends explicitly;
        // returning from main would leave SDK worker threads alive indefinitely.
        android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
        if (launchActivity) mainHandler.post(new Runnable() {
            @Override public void run() {
                try { SdActivityHost.launchMainActivity(activityApk); }
                catch (Throwable failure) {
                    fail("Activity launch", failure);
                    Runtime.getRuntime().halt(10);
                }
            }
        });
        mainHandler.postDelayed(new Runnable() {
            @Override public void run() {
                if(launchActivity&&System.getProperty("saidroid.window.snapshot")!=null)try{
                    SdSurfaceStore.saveSnapshot(System.getProperty("saidroid.window.snapshot"));
                }catch(Exception failure){fail("Capture actual Android window",failure);Runtime.getRuntime().halt(10);}
                mark("QQ main Looper callback completed");
                mark(launchActivity ? "DONE Activity framework check; display/input unverified"
                        : "DONE initialization-only; no Activity display assertion");
                Runtime.getRuntime().halt(0);
            }
        }, Long.getLong("saidroid.probe.duration_ms",3000));
        mark("Entering Android main Looper");
        android.os.Looper.loop();
    }
}
