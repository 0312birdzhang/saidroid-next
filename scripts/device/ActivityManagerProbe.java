import android.app.ActivityManager;
import android.app.ActivityManagerNative;
import android.app.IActivityManager;
import android.content.pm.ApplicationInfo;
import android.os.IBinder;
import android.os.Process;
import android.os.ServiceManager;

import java.util.List;

/** Exercises the real framework lookup and the process-local service in ART. */
public final class ActivityManagerProbe {
    private static int checks;

    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
        checks++;
    }

    public static void main(String[] args) throws Exception {
        System.load(args[1]);
        require(SdBridge.loadBionicLibrary(args[0] + "/libandroid_runtime.so", args[0]),
                "Framework native library did not load");
        require(SdBridge.registerFrameworkNatives() > 0, "Framework registration failed");
        System.out.println(SdServices.installAll());
        IActivityManager manager = ActivityManagerNative.getDefault();
        IBinder binder = ServiceManager.getService("activity");
        require(manager != null && binder != null, "ActivityManager lookup returned null");
        require(binder.queryLocalInterface("android.app.IActivityManager") == manager,
                "Framework lookup did not preserve the local service");
        require(ActivityManagerNative.asInterface(binder) == manager,
                "ActivityManager's real Binder descriptor did not match");
        require(manager.getRunningAppProcesses().isEmpty(), "Unbound application was invented");

        ApplicationInfo app = new ApplicationInfo();
        app.packageName = "org.saidroid.activitymanager.test";
        app.processName = app.packageName + ":worker";
        SdServices.bindApplication(app);
        SdServices.bindApplication(app); // Same owner can register idempotently.
        require(manager.checkPermission("org.saidroid.permission.not.declared", Process.myPid(),
                Process.myUid()) == android.content.pm.PackageManager.PERMISSION_DENIED,
                "Undeclared permission was granted");
        android.os.Binder token = new android.os.Binder();
        android.content.pm.ActivityInfo activity = new android.content.pm.ActivityInfo();
        activity.packageName = app.packageName;
        activity.name = app.packageName + ".MainActivity";
        SdServices.registerActivity(token, activity, new android.content.Intent()
                .setClassName(activity.packageName, activity.name), SdDisplayShim.DISPLAY_ID);
        require(manager.getActivityDisplayId(token) == SdDisplayShim.DISPLAY_ID,
                "Activity display did not come from the host registration");
        require(manager.getActivityOptions(token) == null, "Launch options were invented");
        manager.setTaskDescription(token, new ActivityManager.TaskDescription("SaiDroid task metadata"));
        require(manager.getTaskForActivity(token, false) > 0
                && "SaiDroid task metadata".equals(SdServices.getActivityTaskDescription(token).getLabel()),
                "Task metadata was not retained for the window host");
        try {
            manager.getActivityDisplayId(new android.os.Binder());
            throw new AssertionError("Unknown Activity token was accepted");
        } catch (IllegalArgumentException expected) { checks++; }
        List<ActivityManager.RunningAppProcessInfo> result = manager.getRunningAppProcesses();
        require(result.size() == 1, "Expected exactly the hosted application");
        ActivityManager.RunningAppProcessInfo process = result.get(0);
        require(process.pid == Process.myPid() && process.uid == Process.myUid(),
                "Process identity did not come from this Linux process");
        require(app.processName.equals(process.processName)
                && app.packageName.equals(process.pkgList[0]), "Bound application identity changed");
        require(process.importance == ActivityManager.RunningAppProcessInfo.IMPORTANCE_BACKGROUND,
                "Query incorrectly claimed that a window was resumed");
        process.pkgList[0] = "modified.by.caller";
        result.clear();
        require(app.packageName.equals(manager.getRunningAppProcesses().get(0).pkgList[0]),
                "Caller changed the service's process registry");

        SdServices.setActivityResumed(true);
        ActivityManager.RunningAppProcessInfo state = new ActivityManager.RunningAppProcessInfo();
        manager.getMyMemoryState(state);
        require(state.pid == Process.myPid()
                && state.importance == ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND
                && state.processState == ActivityManager.PROCESS_STATE_TOP,
                "Resumed state was not propagated");
        SdServices.setActivityResumed(false);
        require(manager.getPackageProcessState(app.packageName, app.packageName)
                == ActivityManager.PROCESS_STATE_CACHED_EMPTY, "Background state was not propagated");
        require(manager.getPackageProcessState("unknown.package", app.packageName)
                == ActivityManager.PROCESS_STATE_NONEXISTENT, "Unknown package was invented");

        ApplicationInfo other = new ApplicationInfo();
        other.packageName = "another.application";
        try {
            SdServices.bindApplication(other);
            throw new AssertionError("Another application replaced the process owner");
        } catch (IllegalStateException expected) {
            checks++;
        }
        try {
            manager.isUserAMonkey();
            throw new AssertionError("Unsupported operation silently succeeded");
        } catch (UnsupportedOperationException expected) {
            checks++;
        }
        require(ActivityManagerNative.getDefault().asBinder() == binder,
                "Service owner changed after process queries");
        System.out.println("ACTIVITY_MANAGER_TESTS=PASS|checks=" + checks
                + "|pid=" + Process.myPid() + "|uid=" + Process.myUid());
    }
}
