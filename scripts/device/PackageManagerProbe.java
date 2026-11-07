import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.IPackageManager;
import android.content.pm.PackageManager;
import android.os.Process;

/** Unknown package answers must not accidentally identify the hosted APK. */
public final class PackageManagerProbe {
    private static int checks;

    private static void require(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
        checks++;
    }

    public static void main(String[] args) throws Exception {
        System.load(args[1]);
        require(SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0]), "natives");
        SdBridge.registerFrameworkNatives();
        SdServices.installAll();
        android.os.Looper.prepareMainLooper();
        android.app.ActivityThread thread = android.app.ActivityThread.systemMain();
        java.lang.reflect.Method create = Class.forName("android.app.ContextImpl")
                .getDeclaredMethod("createSystemContext", android.app.ActivityThread.class);
        create.setAccessible(true);
        PackageManager pm = ((Context) create.invoke(null, thread)).getPackageManager();
        ApplicationInfo qq = pm.getApplicationInfo("com.tencent.mobileqq", 0);
        require(qq.uid == Process.myUid(), "Package UID differs from the real hosted process");
        require("com.tencent.mobileqq".equals(qq.packageName), "Hosted package identity");
        require("android".equals(pm.getApplicationInfo("android", 0).packageName), "Framework package");
        String unknown = "org.saidroid.package.that.is.not.installed";
        try {
            pm.getApplicationInfo(unknown, 0);
            throw new AssertionError("Unknown application was reported as QQ");
        } catch (PackageManager.NameNotFoundException expected) {
            checks++;
        }
        try {
            pm.getPackageInfo(unknown, 0);
            throw new AssertionError("Unknown package was reported as QQ");
        } catch (PackageManager.NameNotFoundException expected) {
            checks++;
        }
        IPackageManager raw = android.app.ActivityThread.getPackageManager();
        require(raw.getPackageUid(unknown, 0) == -1, "Unknown package UID");
        require(!raw.isPackageAvailable(unknown, 0), "Unknown package availability");
        require(raw.getPackagesForUid(Integer.MAX_VALUE) == null, "Unknown UID package list");
        require(raw.checkPermission("android.permission.INTERNET", unknown, 0)
                == PackageManager.PERMISSION_DENIED, "Unknown package permission");
        require(raw.checkPermission("android.permission.INTERNET", qq.packageName, 0)
                == PackageManager.PERMISSION_GRANTED, "Declared normal platform permission");
        require(raw.checkUidPermission("android.permission.INTERNET", Process.myUid())
                == PackageManager.PERMISSION_GRANTED, "Installed UID normal permission");
        require(raw.checkPermission("android.permission.READ_SMS", qq.packageName, 0)
                == PackageManager.PERMISSION_DENIED, "Dangerous permission without grant");
        require(raw.checkPermission("android.permission.INTERACT_ACROSS_USERS_FULL", qq.packageName, 0)
                == PackageManager.PERMISSION_DENIED, "Signature permission without platform signature");
        require(pm.getInstalledApplications(0).size() == 2, "Installed runtime package inventory");
        require(Process.myUid() > 0, "APK checks must use an application user, not root");
        require(android.os.Environment.MEDIA_MOUNTED.equals(
                android.os.Environment.getExternalStorageState()), "Primary emulated storage state");
        java.io.File external = android.os.Environment.getExternalStorageDirectory();
        require(external.isDirectory() && external.canWrite(), "Primary storage is not writable");
        System.out.println("PACKAGE_MANAGER_TESTS=PASS|checks=" + checks);
    }
}
