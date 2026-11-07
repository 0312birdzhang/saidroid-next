/** Required runtime/framework packages, including packages outside android.*. */
public final class RuntimePrerequisitesProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[1]);
        if (!SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0])) {
            throw new IllegalStateException("Framework natives unavailable");
        }
        SdBridge.registerFrameworkNatives();
        String[] names = {
                "org.json.JSONObject", "org.json.JSONArray",
                "org.xmlpull.v1.XmlPullParser", "org.xmlpull.v1.XmlPullParserException",
                "javax.microedition.khronos.egl.EGL10",
                "javax.microedition.khronos.opengles.GL10",
                "com.google.android.collect.Maps", "com.google.android.collect.Lists",
                "com.google.android.collect.Sets",
                "android.icu.util.TimeZone", "android.icu.text.SimpleDateFormat",
                "libcore.icu.LocaleData"
        };
        int missing = 0;
        for (String name : names) {
            try {
                Class.forName(name, false, null);
                System.out.println("FRAMEWORK_CLASS=present|name=" + name);
            } catch (Throwable error) {
                missing++;
                System.out.println("FRAMEWORK_CLASS=missing|name=" + name + "|error=" + error);
            }
        }
        int zones = java.util.TimeZone.getAvailableIDs().length;
        System.out.println("TIMEZONE_DATABASE=zones|count=" + zones);
        if (missing != 0 || zones <= 1) {
            throw new AssertionError("Runtime prerequisites: missing=" + missing + " zones=" + zones);
        }
        java.io.File file = new java.io.File(args[4], "preferences.xml");
        if (file.exists()) throw new AssertionError("Preserve existing preference test file");
        java.lang.reflect.Constructor<?> constructor = Class.forName("android.app.SharedPreferencesImpl")
                .getDeclaredConstructor(java.io.File.class, int.class);
        constructor.setAccessible(true);
        android.content.SharedPreferences preferences =
                (android.content.SharedPreferences) constructor.newInstance(file, 0);
        if (!preferences.edit().putString("runtime", "ART").putInt("format", 1).commit()) {
            throw new AssertionError("SharedPreferences commit failed");
        }
        android.content.SharedPreferences reopened =
                (android.content.SharedPreferences) constructor.newInstance(file, 0);
        if (!"ART".equals(reopened.getString("runtime", null)) || reopened.getInt("format", 0) != 1) {
            throw new AssertionError("SharedPreferences persisted values changed");
        }
        System.out.println("SHARED_PREFERENCES=PASS|write=true|reopen=true");
        System.out.println("RUNTIME_PREREQUISITES=PASS|classes=" + names.length + "|zones=" + zones);
    }
}
