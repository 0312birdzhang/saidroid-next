import java.io.File;
import java.io.FileInputStream;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/** Verify every configured font before native Typeface initialization and drawing. */
public final class FontRuntimeProbe {
    private static Object field(Object object, String name) throws Exception {
        Field field = object.getClass().getDeclaredField(name);
        field.setAccessible(true);
        return field.get(object);
    }
    public static void main(String[] args) throws Exception {
        Class<?> parser = Class.forName("android.graphics.FontListParser");
        Method parse = parser.getDeclaredMethod("parse", java.io.InputStream.class);
        parse.setAccessible(true);
        Object configuration;
        try (FileInputStream input = new FileInputStream("/home/art/etc/fonts.xml")) {
            configuration = parse.invoke(null, input);
        }
        int files = 0;
        for (Object family : (Iterable<?>) field(configuration, "families")) {
            for (Object font : (Iterable<?>) field(family, "fonts")) {
                String name = (String) field(font, "fontName");
                File file = new File(name);
                if (!name.startsWith("/home/art/fonts/") || !file.isFile()
                        || !file.canRead() || file.length() < 1000) {
                    throw new AssertionError("Configured font is unavailable: " + name);
                }
                files++;
            }
        }
        if (files < 20) throw new AssertionError("Real fallback font list was not parsed");
        System.out.println("FONT_PREFLIGHT=PASS|configured_fonts=" + files);
        System.load(args[1]);
        if (!SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0])) {
            throw new IllegalStateException("Framework natives unavailable");
        }
        SdBridge.registerFrameworkNatives();
        android.graphics.Paint defaultPaint = new android.graphics.Paint();
        defaultPaint.setTextSize(36);
        if (defaultPaint.measureText("Native default font") <= 0) {
            throw new AssertionError("Skia native default font backend is unavailable");
        }
        System.out.println("NATIVE_DEFAULT_FONT=PASS");
        android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        paint.setTypeface(android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.NORMAL));
        paint.setTextSize(36);
        paint.setColor(0xffffffff);
        if (!paint.hasGlyph("中") || paint.measureText("SailDroid 中文") <= 0) {
            throw new AssertionError("Native Latin/CJK typeface shaping failed");
        }
        android.graphics.Bitmap bitmap = android.graphics.Bitmap.createBitmap(400, 80,
                android.graphics.Bitmap.Config.ARGB_8888);
        new android.graphics.Canvas(bitmap).drawText("SailDroid 中文", 8, 50, paint);
        int[] pixels = new int[400 * 80];
        bitmap.getPixels(pixels, 0, 400, 0, 0, 400, 80);
        int covered = 0;
        for (int pixel : pixels) if ((pixel >>> 24) != 0) covered++;
        bitmap.recycle();
        if (covered < 100) throw new AssertionError("Native Canvas did not draw real glyph pixels");
        System.out.println("FONT_RUNTIME_TESTS=PASS|cjk_glyph=true|covered_pixels=" + covered);
    }
}
