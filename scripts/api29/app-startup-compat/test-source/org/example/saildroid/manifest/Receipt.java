package org.example.saildroid.manifest;
import android.app.Application;
import android.content.*;
import android.os.*;
import java.io.FileOutputStream;
import org.json.JSONObject;
final class Receipt {
    static void write(Context context, Intent intent) {
        String name = intent.getStringExtra("name");
        if (!name.matches("local|async|remote|protected|forbidden")) throw new AssertionError("Unknown receipt");
        try {
            JSONObject row = new JSONObject();
            row.put("main", Looper.myLooper() == Looper.getMainLooper());
            row.put("restricted", context.getClass().getName().equals("android.app.ReceiverRestrictedContext"));
            row.put("application_loader", LocalReceiver.class.getClassLoader() != Object.class.getClassLoader());
            row.put("pid", android.os.Process.myPid()); row.put("process", Application.getProcessName());
            row.put("payload", intent.getIntExtra("payload", -1)); row.put("name", name);
            try (FileOutputStream output = context.openFileOutput(name+".json", Context.MODE_PRIVATE)) {
                output.write(row.toString().getBytes("UTF-8"));
            }
            System.err.println("MANIFEST_FIXTURE=received|name="+name+"|pid="+android.os.Process.myPid());
        } catch (Exception failure) { throw new RuntimeException(failure); }
    }
}
