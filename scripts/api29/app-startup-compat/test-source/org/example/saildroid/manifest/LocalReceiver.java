package org.example.saildroid.manifest;
import android.content.*;
import android.os.*;
public final class LocalReceiver extends BroadcastReceiver {
    public void onReceive(final Context context, final Intent intent) {
        if ("async".equals(intent.getStringExtra("name"))) {
            final PendingResult pending = goAsync();
            new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
                public void run() { try { Receipt.write(context,intent); } finally { pending.finish(); } }
            }, 50);
        } else Receipt.write(context,intent);
    }
}
