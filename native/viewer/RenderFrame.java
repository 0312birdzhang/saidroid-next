import java.io.*;

public class RenderFrame {
    static final int W = 1080, H = 2160;
    public static void main(String[] a) throws Exception {
        System.out.println("RENDER_START");
        System.load("/home/art/lib/libsdbridge.so");
        boolean ok = SdBridge.loadBionicLibrary("/home/art/bio2/libandroid_runtime.so", "/home/art/bio2");
        int reg = ok ? SdBridge.registerFrameworkNatives() : -1;
        System.out.println("BOOTSTRAP load=" + ok + " registered=" + reg);
        if (!ok) return;
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(W, H,
                android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(b);
        android.graphics.Paint p = new android.graphics.Paint();
        p.setAntiAlias(true);

        // 渐变背景
        p.setShader(new android.graphics.LinearGradient(0, 0, 0, H,
                0xFF0B1B3A, 0xFF1B4B8F, android.graphics.Shader.TileMode.CLAMP));
        c.drawRect(0, 0, W, H, p);
        p.setShader(null);

        // 图形
        p.setColor(0xFF2196F3); c.drawCircle(W / 2, 620, 260, p);
        p.setColor(0xFFFFC107); c.drawRect(120, 980, 960, 1120, p);
        p.setColor(0xFF43A047); c.drawRoundRect(new android.graphics.RectF(120, 1180, 960, 1320), 40, 40, p);

        // 文字：NO_TEXT_YET —— 当前未提供 Android 字体配置，先验证像素通路
        p.setColor(0xFFFFFFFF);
        c.drawRect(90, 240, 700, 300, p);
        c.drawRect(90, 330, 520, 380, p);

        int[] pix = new int[W * H];
        b.getPixels(pix, 0, W, 0, 0, W, H);
        System.out.println("PIXELS " + pix.length + " sample=" + Integer.toHexString(pix[H/2*W + W/2]));
        FileOutputStream fo = new FileOutputStream("/home/art/frame.rgba");
        fo.write("SDRGBA\0".getBytes());
        java.nio.ByteBuffer bb = java.nio.ByteBuffer.allocate(8).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        bb.putInt(W); bb.putInt(H);
        fo.write(bb.array());
        java.nio.ByteBuffer pb = java.nio.ByteBuffer.allocate(W * H * 4).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        for (int v : pix) pb.putInt(v);
        fo.write(pb.array());
        fo.close();
        System.out.println("RENDER_DONE");
    }
}
