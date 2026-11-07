import android.content.res.Resources;

/** Framework private IDs must resolve against the same classes' resource table. */
public final class FrameworkResourcesProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[1]);
        if (!SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0])) {
            throw new IllegalStateException("Framework natives unavailable");
        }
        SdBridge.registerFrameworkNatives();
        SdServices.installAll();
        android.os.Looper.prepareMainLooper();
        SdActivityHost.applyDisplayConfiguration(android.app.ActivityThread.systemMain());
        Resources resources = Resources.getSystem();
        int dock = 0x010e00b9; // The original PhoneWindow.DecorView constructor's ID.
        String name = resources.getResourceName(dock);
        int duration = resources.getInteger(dock);
        if (!"android:integer/dock_enter_exit_duration".equals(name) || duration <= 0) {
            throw new AssertionError("PhoneWindow's actual private resource ID does not match");
        }
        if (resources.getString(android.R.string.ok).length() == 0) {
            throw new AssertionError("Public framework string resource missing");
        }
        int lookup = resources.getIdentifier("ok", "string", "android");
        System.out.println("FRAMEWORK_RESOURCES_TESTS=PASS|phone_window_resource=" + name
                + "|duration=" + duration + "|public_name_lookup=" + lookup);
    }
}
