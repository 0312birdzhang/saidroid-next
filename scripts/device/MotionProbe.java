public class MotionProbe {
    public static void main(String[] a) {
        System.out.println("MOTION_START");
        System.load("/home/art/lib/libsdbridge.so");
        boolean ok = SdBridge.loadBionicLibrary("/home/art/bio2/libandroid_runtime.so", "/home/art/bio2");
        int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
        System.out.println("BOOTSTRAP load=" + ok + " reg=" + reg);
        if (!ok) return;
        try {
            long now = android.os.SystemClock.uptimeMillis();
            android.view.MotionEvent ev = android.view.MotionEvent.obtain(
                    now, now, android.view.MotionEvent.ACTION_DOWN, 270f, 540f, 0);
            System.out.println("MOTION_OK action=" + ev.getAction() + " x=" + ev.getX() + " y=" + ev.getY()
                    + " downTime=" + ev.getDownTime());
            android.view.MotionEvent up = android.view.MotionEvent.obtain(
                    now, now + 50, android.view.MotionEvent.ACTION_UP, 270f, 540f, 0);
            System.out.println("MOTION_UP action=" + up.getAction());
            ev.recycle(); up.recycle();
            System.out.println("MOTION_DONE");
        } catch (Throwable t) {
            Throwable c = t; while (c.getCause() != null) c = c.getCause();
            System.out.println("MOTION_FAIL " + c.getClass().getName() + ": " + c.getMessage());
        }
    }
}
