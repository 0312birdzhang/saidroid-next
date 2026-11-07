package com.macapk.loader;

/**
 * NativeLog 的纯 Java 实现。
 *
 * Mac.apk 原本用 native 库输出日志，Sailfish 上不需要，
 * 直接转发到 System.out/err。
 *
 * 框架调用的方法：v/d/i/w/e/print
 */
public final class NativeLog {
    private NativeLog() {}

    public static void v(String tag, String msg) { print(2, tag, msg); }
    public static void d(String tag, String msg) { print(3, tag, msg); }
    public static void i(String tag, String msg) { print(4, tag, msg); }
    public static void w(String tag, String msg) { print(5, tag, msg); }
    public static void e(String tag, String msg) { print(6, tag, msg); }

    public static void print(int priority, String tag, String msg) {
        String line = "[" + levelName(priority) + "] "
                    + (tag == null ? "?" : tag) + ": "
                    + (msg == null ? "" : msg);
        if (priority >= 5) System.err.println(line);
        else System.out.println(line);
    }

    private static String levelName(int p) {
        switch (p) {
            case 2: return "V";
            case 3: return "D";
            case 4: return "I";
            case 5: return "W";
            case 6: return "E";
            default: return "?";
        }
    }
}
