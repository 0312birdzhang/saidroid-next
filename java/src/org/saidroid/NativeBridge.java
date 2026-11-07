package org.saidroid;

/**
 * Java 与原生 GLES 渲染器的桥接。
 * 原生库导出：init / setCallback / drawFrame / shutdown / inputCount
 */
public class NativeBridge {
    static {
        System.loadLibrary("saidroid_jni");
    }

    public static native boolean init(int w, int h);
    public static native void setCallback(Object obj);
    public static native boolean drawFrame(int[] argb, int w, int h);
    public static native void shutdown();
    public static native int inputCount(int which);  // 0=ptr 1=touch 2=key

    /** 原生回调入口 */
    public static void onNativeInput(String type, int a, int b, int c) {
        System.out.println("  [input] " + type + " a=" + a + " b=" + b + " c=" + c);
    }

    /** 端到端测试 */
    public static void main(String[] args) throws Exception {
        int W = 1080, H = 2160;
        int CW = 540, CH = 1080;
        int frames = args.length > 0 ? Integer.parseInt(args[0]) : 30;

        System.out.println("jni_test=start|frames=" + frames);

        if (!init(W, H)) {
            System.out.println("jni_test=fail|init");
            return;
        }
        System.out.println("jni_test=native_ready");
        setCallback(new Object());

        CanvasBridge canvas = new CanvasBridge(CW, CH);
        System.out.println("jni_test=canvas_ready");

        long t0 = System.nanoTime();
        for (int f = 0; f < frames; f++) {
            canvas.drawFrame(f);
            int[] px = canvas.getPixels();
            if (!drawFrame(px, CW, CH)) {
                System.out.println("jni_test=fail|draw@" + f);
                break;
            }
            if (f == 0 || f == frames/2 || f == frames-1)
                System.out.println("jni_test=frame_" + f);
        }
        long t1 = System.nanoTime();
        double ms = (t1 - t0) / 1e6;

        System.out.println("jni_test=rendered|frames=" + frames
            + "|total_ms=" + String.format("%.1f", ms)
            + "|per_frame_ms=" + String.format("%.2f", ms / frames));
        System.out.println("jni_test=ptr=" + inputCount(0)
            + "|touch=" + inputCount(1) + "|key=" + inputCount(2));
        shutdown();
        System.out.println("jni_test=OK");
    }
}
