public class NativeProbe4 {
    interface T { String run() throws Throwable; }
    static void check(String name, T body) {
        try { System.out.println("OK   " + name + " = " + body.run()); }
        catch (Throwable t) {
            Throwable c = t; while (c.getCause() != null) c = c.getCause();
            System.out.println("FAIL " + name + " : " + c.getClass().getName() + ": " + c.getMessage());
        }
    }
    public static void main(String[] a) {
        System.out.println("NP4_START");
        // WARMUP：先把 VMRuntime 类初始化好，避免 native 侧 gVMRuntime 在注册期拿到空
        try {
            Class<?> vmrc = Class.forName("dalvik.system.VMRuntime");
            System.out.println("WARMUP VMRuntime=" + vmrc.getMethod("getRuntime").invoke(null));
            Class.forName("java.lang.Byte");
        } catch (Throwable t) {
            System.out.println("WARMUP FAIL " + t);
        }
        System.load("/home/art/lib/libsdbridge.so");
        boolean ok = SdBridge.loadBionicLibrary("/home/art/bio2/libandroid_runtime.so", "/home/art/bio2");
        System.out.println("SDBRIDGE_LOAD=" + ok);
        if (!ok) return;
        int n = SdBridge.registerFrameworkNatives();
        System.out.println("SDBRIDGE_REGISTERED=" + n);
        check("VMRuntime.getRuntime", new T() { public String run() throws Throwable {
            Class<?> c = Class.forName("dalvik.system.VMRuntime");
            Object o = c.getMethod("getRuntime").invoke(null);
            return String.valueOf(o); } });
        check("VMRuntime static init", new T() { public String run() throws Throwable {
            Class<?> c = Class.forName("dalvik.system.VMRuntime", true, NativeProbe4.class.getClassLoader());
            return c.getName() + " initOK"; } });
        System.out.println("SELFTest " + SdBridge.selfTestVmRuntime());
        System.out.println("GraphicsInit " + SdBridge.checkGraphicsInit());
        check("Log.isLoggable", new T() { public String run() { return String.valueOf(android.util.Log.isLoggable("p", 4)); } });
        check("SystemClock.elapsedRealtime", new T() { public String run() { return String.valueOf(android.os.SystemClock.elapsedRealtime()); } });
        check("Bitmap.createBitmap", new T() { public String run() {
            android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(64, 64, android.graphics.Bitmap.Config.ARGB_8888);
            return b == null ? "null" : (b.getWidth() + "x" + b.getHeight() + " rowBytes=" + b.getRowBytes()); } });
        check("Canvas.drawRect+getPixel", new T() { public String run() {
            android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(64, 64, android.graphics.Bitmap.Config.ARGB_8888);
            android.graphics.Canvas c = new android.graphics.Canvas(b);
            android.graphics.Paint p = new android.graphics.Paint();
            p.setColor(0xFFFF0000);
            c.drawRect(8, 8, 56, 56, p);
            return "center=" + Integer.toHexString(b.getPixel(32, 32)) + " corner=" + Integer.toHexString(b.getPixel(1, 1)); } });
        check("Looper.prepareMainLooper", new T() { public String run() {
            android.os.Looper.prepareMainLooper();
            return String.valueOf(android.os.Looper.getMainLooper()); } });
        System.out.println("NP4_DONE");
    }
}
