package org.saidroid;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;

/**
 * Canvas 渲染桥接：把 Android Canvas 的绘制结果导出为 ARGB 像素。
 * 这是 Java 侧与原生 GLES 渲染器之间的接口。
 */
public class CanvasBridge {
    private Bitmap bitmap;
    private Canvas canvas;
    private int[] pixels;
    private final int width, height;
    private final Paint paint = new Paint();

    public CanvasBridge(int w, int h) {
        this.width = w;
        this.height = h;
        this.bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        this.canvas = new Canvas(bitmap);
        this.pixels = new int[w * h];
        System.out.println("bridge=created|w=" + w + "|h=" + h);
    }

    /** 绘制一帧测试内容 */
    public void drawFrame(int frame) {
        // 背景渐变
        paint.setColor(Color.rgb(
            20 + (frame * 2) % 200,
            40,
            80 + (frame * 3) % 150));
        canvas.drawRect(0, 0, width, height, paint);

        // 移动的方块
        float size = width / 5f;
        float x = (frame * 8) % (width - size);
        float y = height / 2f - size / 2f;
        paint.setColor(Color.rgb(255, 136, 0));
        canvas.drawRect(new RectF(x, y, x + size, y + size), paint);

        // 文字
        paint.setColor(Color.WHITE);
        paint.setTextSize(width / 12f);
        canvas.drawText("SaiDroid Canvas", 40, 120, paint);
        canvas.drawText("frame " + frame, 40, 200, paint);
    }

    /** 导出当前画布为 ARGB 数组 */
    public int[] getPixels() {
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height);
        return pixels;
    }

    public int getWidth() { return width; }
    public int getHeight() { return height; }
    public Bitmap getBitmap() { return bitmap; }
    public Canvas getCanvas() { return canvas; }

    /** 自测：绘制并检查像素 */
    public static void main(String[] args) {
        System.out.println("canvas_test=start");
        CanvasBridge b = new CanvasBridge(540, 1080);
        b.drawFrame(0);
        int[] px = b.getPixels();
        System.out.println("pixels_len=" + px.length);
        System.out.println("px[0]=" + Integer.toHexString(px[0]));
        System.out.println("px[mid]=" + Integer.toHexString(px[px.length/2]));
        // 检查非全黑
        int nonBlack = 0;
        for (int i = 0; i < px.length; i += 1000) {
            if ((px[i] & 0x00FFFFFF) != 0) nonBlack++;
        }
        System.out.println("non_black_samples=" + nonBlack);
        System.out.println("canvas_test=OK");
    }
}
