package org.example.saildroid.manifest;
import android.content.*;
public final class DisabledReceiver extends BroadcastReceiver {
    public void onReceive(Context context, Intent intent) { Receipt.write(context,intent); }
}
