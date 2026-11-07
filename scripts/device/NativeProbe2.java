public class NativeProbe2 {
    interface T { String run() throws Throwable; }
    static void check(String name, T body) {
        try { System.out.println("OK   " + name + " = " + body.run()); }
        catch (Throwable t) {
            Throwable c = t; while (c.getCause() != null) c = c.getCause();
            System.out.println("FAIL " + name + " : " + c.getClass().getName() + ": " + c.getMessage());
        }
    }
    public static void main(String[] a) {
        System.out.println("NP2_START");
        System.load("/home/art/lib/libsdbridge.so");
        boolean ok = SdBridge.loadBionicLibrary("/home/art/bio2/libandroid_runtime.so", "/home/art/bio2");
        System.out.println("SDBRIDGE_LOAD = " + ok);
        if (!ok) return;
        check("Log.isLoggable", new T() { public String run() { return String.valueOf(android.util.Log.isLoggable("p", 4)); } });
        check("SystemClock.elapsedRealtime", new T() { public String run() { return String.valueOf(android.os.SystemClock.elapsedRealtime()); } });
        check("Bitmap.createBitmap", new T() { public String run() {
            android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(64, 64, android.graphics.Bitmap.Config.ARGB_8888);
            return b == null ? "null" : (b.getWidth() + "x" + b.getHeight() + " @" + b.getRowBytes()); } });
        check("Bitmap pixel roundtrip", new T() { public String run() {
            android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(2, 1, android.graphics.Bitmap.Config.ARGB_8888);
            b.setPixel(0, 0, 0xFF112233);
            b.setPixel(1, 0, 0xFFAABBCC);
            return Integer.toHexString(b.getPixel(0,0)) + "," + Integer.toHexString(b.getPixel(1,0)); } });
        check("Canvas draw", new T() { public String run() {
            android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(100, 100, android.graphics.Bitmap.Config.ARGB_8888);
            android.graphics.Canvas c = new android.graphics.Canvas(b);
            android.graphics.Paint p = new android.graphics.Paint();
            p.setColor(0xFFFF0000);
            c.drawRect(10, 10, 90, 90, p);
            return Integer.toHexString(b.getPixel(50,50)); } });
        check("Looper.prepareMainLooper", new T() { public String run() {
            android.os.Looper.prepareMainLooper();
            return String.valueOf(android.os.Looper.getMainLooper()); } });
        System.out.println("NP2_DONE");
    }
}
