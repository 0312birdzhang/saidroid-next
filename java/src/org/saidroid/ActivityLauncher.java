package org.saidroid;

import android.app.Activity;
import android.app.ActivityThread;
import android.app.Application;
import android.app.Instrumentation;
import android.content.Intent;
import android.os.Bundle;

import java.io.File;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.List;

/**
 * Activity 启动器：把转换好的 APK 真正跑起来。
 *
 * 流程：
 *   1. 组装 classpath（app jar + framework）
 *   2. ActivityThread.macapkBindApplication → 创建 Application
 *   3. Instrumentation.newActivity → 创建 Activity 实例
 *   4. callActivityOnCreate → 触发 onCreate
 *   5. onStart / onResume
 */
public class ActivityLauncher {

    public static class LaunchResult {
        public boolean ok;
        public String stage;
        public String error;
        public Application application;
        public Activity activity;
        public String toString() {
            return ok ? "LAUNCH=ok|stage=" + stage
                      : "LAUNCH=fail|stage=" + stage + "|" + error;
        }
    }

    private static LaunchResult fail(String stage, Throwable t) {
        LaunchResult r = new LaunchResult();
        r.ok = false;
        r.stage = stage;
        r.error = t.getClass().getSimpleName() + ": " + t.getMessage();
        return r;
    }

    /**
     * 启动 APK 的入口 Activity
     *
     * @param appJar      DexConverter 转换产物
     * @param frameworkJar android-framework.jar
     * @param packageName APK 包名
     * @param activityName 入口 Activity 全名
     */
    public static LaunchResult launch(File appJar, File frameworkJar,
                                      String packageName, String activityName) {
        LaunchResult r = new LaunchResult();
        r.stage = "classpath";

        try {
            // 1. 组装 classpath
            List<URL> urls = new ArrayList<>();
            urls.add(appJar.toURI().toURL());
            if (frameworkJar != null && frameworkJar.exists()) {
                urls.add(frameworkJar.toURI().toURL());
            }
            ClassLoader cl = new URLClassLoader(urls.toArray(new URL[0]),
                                                ActivityLauncher.class.getClassLoader());
            System.out.println("Launch=classpath|app=" + appJar.getName()
                + "|framework=" + (frameworkJar != null && frameworkJar.exists()));

            // 2. 绑定 Application
            r.stage = "bind_application";
            ActivityThread at = ActivityThread.currentActivityThread();
            if (at == null) {
                r.stage = "activity_thread";
                r.error = "currentActivityThread() returned null";
                return r;
            }
            System.out.println("Launch=activity_thread|" + at.getProcessName());

            // Application 类名（从 AndroidManifest 的 application android:name 取，
            // 缺省用 android.app.Application）
            String appClass = "android.app.Application";
            Application app = at.macapkBindApplication(
                packageName, packageName, appClass, cl);
            if (app == null) {
                r.stage = "bind_application";
                r.error = "macapkBindApplication returned null";
                return r;
            }
            r.application = app;
            System.out.println("Launch=application|" + app.getClass().getName());

            // 3. 创建 Activity
            r.stage = "new_activity";
            Instrumentation instr = at.getInstrumentation();
            if (instr == null) {
                r.stage = "instrumentation";
                r.error = "getInstrumentation() returned null";
                return r;
            }

            Class<?> actCls = cl.loadClass(activityName);
            System.out.println("Launch=activity_class|" + actCls.getName());

            Activity act = instr.newActivity(cl, activityName, new Intent());
            if (act == null) {
                r.stage = "new_activity";
                r.error = "newActivity returned null";
                return r;
            }
            r.activity = act;
            System.out.println("Launch=activity_created|" + act.getClass().getName());

            // 4. 生命周期
            r.stage = "onCreate";
            instr.callActivityOnCreate(act, new Bundle());
            System.out.println("Launch=onCreate_ok");

            r.stage = "onStart";
            invokeProtected(act, "onStart");
            System.out.println("Launch=onStart_ok");

            r.stage = "onResume";
            invokeProtected(act, "onResume");
            System.out.println("Launch=onResume_ok");

            r.ok = true;
            r.stage = "resumed";
            return r;

        } catch (Throwable t) {
            System.out.println("Launch=exception|" + t);
            t.printStackTrace();
            return fail(r.stage, t);
        }
    }

    /** 反射调用 protected 生命周期方法 */
    private static void invokeProtected(Activity act, String name) throws Exception {
        Method m = Activity.class.getDeclaredMethod(name);
        m.setAccessible(true);
        m.invoke(act);
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 4) {
            System.err.println("usage: ActivityLauncher <app.jar> <framework.jar> <package> <activity>");
            System.exit(2);
        }
        File appJar = new File(args[0]);
        File fwJar = new File(args[1]);
        LaunchResult r = launch(appJar, fwJar, args[2], args[3]);
        System.out.println(r);
        if (!r.ok) System.exit(1);
    }
}
