import android.content.Intent;
import android.content.pm.PackageParser;
import java.io.File;

/** Inspect real framework-parsed Activity metadata before hosting any Activity. */
public final class ApkManifestProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[1]);
        if (!SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0])) {
            throw new IllegalStateException("Framework natives unavailable");
        }
        SdBridge.registerFrameworkNatives();
        SdServices.installAll();
        PackageParser parser = new PackageParser();
        PackageParser.Package app = parser.parsePackage(new File(args[2]), 0);
        if (!"com.tencent.mobileqq".equals(app.packageName) || app.activities.isEmpty()) {
            throw new AssertionError("Actual QQ package/Activity metadata missing");
        }
        int launchers = 0;
        for (PackageParser.Activity activity : app.activities) {
            for (PackageParser.ActivityIntentInfo filter : activity.intents) {
                if (filter.hasAction(Intent.ACTION_MAIN) && filter.hasCategory(Intent.CATEGORY_LAUNCHER)) {
                    System.out.println("APK_LAUNCHER=parsed|name=" + activity.info.name
                            + "|target=" + activity.info.targetActivity
                            + "|theme=" + activity.info.theme + "|process=" + activity.info.processName);
                    launchers++;
                    break;
                }
            }
        }
        if (launchers == 0) throw new AssertionError("No real launcher Activity found");
        System.out.println("APK_MANIFEST_TESTS=PASS|activities=" + app.activities.size()
                + "|launchers=" + launchers + "|application=" + app.applicationInfo.className
                + "|targetSdk=" + app.applicationInfo.targetSdkVersion);
    }
}
