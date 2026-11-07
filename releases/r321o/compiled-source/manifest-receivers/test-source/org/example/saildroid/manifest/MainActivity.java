package org.example.saildroid.manifest;
import android.app.Activity;
import android.content.*;
import android.os.*;
import android.widget.TextView;
import java.io.File;
import java.nio.file.Files;
import org.json.JSONObject;

public final class MainActivity extends Activity {
    private int dynamicCount;
    private boolean rejectedForeign;
    private final Handler main = new Handler(Looper.getMainLooper());
    private Intent explicit(Class<?> type, String name) {
        return new Intent("org.example.saildroid.manifest.DYNAMIC").setClass(this, type)
                .putExtra("name", name).putExtra("payload", 17);
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TextView view = new TextView(this); view.setText("Private manifest receiver contract"); setContentView(view);
        registerReceiver(new BroadcastReceiver() {
            public void onReceive(Context context, Intent intent) { dynamicCount++; }
        }, new IntentFilter("org.example.saildroid.manifest.DYNAMIC"));
        Intent local = explicit(LocalReceiver.class, "local");
        try { sendBroadcast(local); }
        catch (UnsupportedOperationException failure) {
            if (!"Manifest receivers unavailable".equals(failure.getMessage())) throw failure;
            System.err.println("MANIFEST_FIXTURE=BASELINE_REJECTED|type=explicit-component"); return;
        }
        local.putExtra("payload", 99);
        sendBroadcast(new Intent("org.example.saildroid.manifest.DYNAMIC"));
        sendBroadcast(explicit(LocalReceiver.class, "async").setAction("org.example.saildroid.manifest.ASYNC"));
        sendBroadcast(explicit(RemoteReceiver.class, "remote"));
        sendBroadcast(explicit(ProtectedReceiver.class, "protected"));
        sendBroadcast(explicit(LocalReceiver.class, "forbidden"), "android.permission.READ_CONTACTS");
        sendBroadcast(explicit(DeniedReceiver.class, "forbidden"));
        sendBroadcast(explicit(DisabledReceiver.class, "forbidden"));
        sendBroadcast(explicit(NotDeclaredReceiver.class, "forbidden"));
        try {
            sendBroadcast(new Intent("org.example.saildroid.manifest.DYNAMIC")
                    .setComponent(new ComponentName("org.example.other", "org.example.other.Receiver")));
        } catch (SecurityException expected) { rejectedForeign = true; }
        final long deadline = SystemClock.uptimeMillis() + 45000;
        main.postDelayed(new Runnable() {
            private long allReadyAt;
            public void run() {
                try {
                    boolean ready = true;
                    for (String name : new String[]{"local", "async", "remote", "protected"}) {
                        File file = new File(getFilesDir(), name + ".json");
                        if (!file.isFile()) { ready = false; continue; }
                        JSONObject row = new JSONObject(new String(Files.readAllBytes(file.toPath()), "UTF-8"));
                        if (!row.getBoolean("main") || !row.getBoolean("restricted") ||
                                !row.getBoolean("application_loader") || row.getInt("payload") != 17)
                            throw new AssertionError("Receiver callback contract: " + name);
                        if (name.equals("remote")) {
                            if (row.getInt("pid") == android.os.Process.myPid() ||
                                    !row.getString("process").equals(getPackageName()+":receiver"))
                                throw new AssertionError("Remote receiver did not run in its declared process");
                        } else if (row.getInt("pid") != android.os.Process.myPid()) throw new AssertionError("Local receiver process");
                    }
                    if (new File(getFilesDir(), "forbidden.json").exists()) throw new AssertionError("Forbidden receiver executed");
                    if (dynamicCount > 1) throw new AssertionError("Explicit broadcast reached dynamic receiver");
                    if (ready && dynamicCount == 1 && rejectedForeign) {
                        if (allReadyAt == 0) allReadyAt = SystemClock.uptimeMillis();
                        if (SystemClock.uptimeMillis() - allReadyAt >= 1500) {
                            System.err.println("MANIFEST_FIXTURE=PASS|local=1|async=1|remote=1|protected=1|dynamic=1|negative=5|payload=17");
                            return;
                        }
                    }
                    if (SystemClock.uptimeMillis() > deadline) throw new AssertionError("Receiver receipt deadline");
                    main.postDelayed(this, 100);
                } catch (Throwable failure) { throw new RuntimeException(failure); }
            }
        }, 100);
    }
}
