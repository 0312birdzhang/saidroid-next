import android.app.ActivityManagerNative;
import android.app.IActivityManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.IIntentReceiver;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.ApplicationInfo;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Process;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Real Binder-local broadcasts plus the framework's Context/Handler dispatcher. */
public final class BroadcastProbe {
    private static int checks;
    private static void require(boolean value, String detail) {
        if (!value) throw new AssertionError(detail);
        checks++;
    }
    private static void send(IActivityManager manager, Intent intent, int user) throws Exception {
        manager.broadcastIntent(null, intent, null, null, 0, null, null,
                null, -1, null, false, false, user);
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
        Context system = (Context) create.invoke(null, thread);
        final String pkg = "com.tencent.mobileqq";
        ApplicationInfo app = system.getPackageManager().getApplicationInfo(pkg, 0);
        SdServices.bindApplication(app);
        IActivityManager manager = ActivityManagerNative.getDefault();
        final int user = Process.myUid() / 100000;
        final int[] calls = {0};
        final int[] sentUser = {-1};
        IIntentReceiver receiver = new IIntentReceiver.Stub() {
            @Override public void performReceive(Intent intent, int code, String data, Bundle extras,
                    boolean ordered, boolean sticky, int sendingUser) {
                require(!ordered && !sticky, "Unexpected broadcast flags");
                require(intent.getIntExtra("value", -1) == 42, "Intent payload lost");
                sentUser[0] = sendingUser;
                calls[0]++;
                intent.setAction("receiver.modified.copy");
            }
        };
        IntentFilter filter = new IntentFilter("org.saidroid.TEST");
        require(manager.registerReceiver(null, pkg, receiver, filter, null, user) == null,
                "Invented sticky Intent");
        // Duplicate filters still yield one delivery per registered Binder.
        manager.registerReceiver(null, pkg, receiver, filter, null, user);
        filter.addAction("org.saidroid.AFTER_REGISTRATION");
        send(manager, new Intent("org.saidroid.AFTER_REGISTRATION"), user);
        require(calls[0] == 0, "Registry retained caller's mutable filter");
        Intent intent = new Intent("org.saidroid.TEST").putExtra("value", 42);
        send(manager, intent, user);
        require(calls[0] == 1 && sentUser[0] == user, "Match/dedup/user delivery failed");
        require("org.saidroid.TEST".equals(intent.getAction()), "Receiver mutated sender Intent");
        manager.unregisterReceiver(receiver);
        send(manager, intent, user);
        require(calls[0] == 1, "Unregistered receiver was called");
        SdAppPermissions permissions = new SdAppPermissions(app.sourceDir, pkg);
        require(!permissions.holds("android.permission.READ_SMS")
                && !permissions.holds("org.saidroid.UNKNOWN_PERMISSION"), "Foreign permission granted");
        require(permissions.holds("android.permission.INTERNET"),
                "Actual requested platform normal permission was denied");
        require(!permissions.getOwnedGrants().isEmpty(), "QQ's actual own permission grants missing");
        String ownPermission = permissions.getOwnedGrants().iterator().next();
        require(manager.checkPermission(ownPermission, Process.myPid(), Process.myUid())
                == android.content.pm.PackageManager.PERMISSION_GRANTED, "Owned permission query denied");
        require(manager.checkPermission(ownPermission, Process.myPid(), Process.myUid() + 1)
                == android.content.pm.PackageManager.PERMISSION_DENIED, "Foreign UID permission query allowed");
        require(manager.checkPermission("android.permission.INTERACT_ACROSS_USERS_FULL",
                Process.myPid(), Process.myUid()) == android.content.pm.PackageManager.PERMISSION_DENIED,
                "Privileged Android permission was invented");
        manager.registerReceiver(null, pkg, receiver, new IntentFilter("org.saidroid.TEST"),
                ownPermission, user);
        send(manager, intent, user);
        require(calls[0] == 2, "Manifest-granted sender was rejected");
        manager.unregisterReceiver(receiver);
        manager.registerReceiver(null, pkg, receiver, new IntentFilter("org.saidroid.TEST"),
                "org.saidroid.UNKNOWN_PERMISSION", user);
        send(manager, intent, user);
        require(calls[0] == 2, "Unauthorized sender reached protected receiver");
        manager.unregisterReceiver(receiver);
        try {
            manager.registerReceiver(null, "another.package", receiver, filter, null, user);
            throw new AssertionError("Foreign package accepted");
        } catch (SecurityException expected) { checks++; }
        try {
            manager.registerReceiver(null, pkg, receiver, filter, null, user + 1);
            throw new AssertionError("Foreign user accepted");
        } catch (SecurityException expected) { checks++; }
        try {
            manager.broadcastIntent(null, intent, null, null, 0, null, null,
                    null, -1, null, true, false, user);
            throw new AssertionError("Ordered broadcast falsely succeeded");
        } catch (UnsupportedOperationException expected) { checks++; }

        // Context's real ReceiverDispatcher must post to the requested Looper.
        android.app.LoadedApk loaded = thread.getPackageInfoNoCheck(app,
                android.content.res.CompatibilityInfo.DEFAULT_COMPATIBILITY_INFO);
        java.lang.reflect.Method createApp = Class.forName("android.app.ContextImpl")
                .getDeclaredMethod("createAppContext", android.app.ActivityThread.class,
                        android.app.LoadedApk.class);
        createApp.setAccessible(true);
        Context context = (Context) createApp.invoke(null, thread, loaded);
        require(pkg.equals(context.getBasePackageName()), "Application Context owner mismatch");
        final HandlerThread worker = new HandlerThread("SaiDroidBroadcastCheck");
        worker.start();
        final CountDownLatch delivered = new CountDownLatch(1);
        final int[] observed = {-1};
        BroadcastReceiver callback = new BroadcastReceiver() {
            @Override public void onReceive(Context context, Intent received) {
                if (Thread.currentThread() == worker && received.getIntExtra("value", -1) == 42) {
                    observed[0] = 42;
                }
                delivered.countDown();
            }
        };
        boolean registered = false;
        try {
            context.registerReceiver(callback, new IntentFilter("org.saidroid.CONTEXT"),
                    null, new Handler(worker.getLooper()));
            registered = true;
            context.sendBroadcast(new Intent("org.saidroid.CONTEXT").putExtra("value", 42));
            require(delivered.await(5, TimeUnit.SECONDS) && observed[0] == 42,
                    "Context broadcast did not reach the requested Handler");
        } finally {
            if (registered) context.unregisterReceiver(callback);
            worker.quitSafely();
            worker.join(5000);
        }
        require(!worker.isAlive(), "Owned HandlerThread did not exit");
        System.out.println("BROADCAST_TESTS=PASS|checks=" + checks + "|uid=" + Process.myUid());
    }
}
