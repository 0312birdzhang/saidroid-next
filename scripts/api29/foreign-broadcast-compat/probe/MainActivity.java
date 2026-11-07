package org.example.saildroid.foreignbroadcast;
import android.app.*;import android.content.*;import android.os.*;import android.widget.*;
public final class MainActivity extends Activity {
 int count; final String action="org.example.saildroid.foreignbroadcast.PING";
 final BroadcastReceiver receiver=new BroadcastReceiver(){public void onReceive(Context c,Intent i){count++;}};
 void require(boolean b,String s){if(!b)throw new AssertionError(s);}
 @Override public void onCreate(Bundle b){super.onCreate(b);TextView v=new TextView(this);v.setText("Broadcast routing test");setContentView(v);registerReceiver(receiver,new IntentFilter(action));
  sendBroadcast(new Intent(action).setPackage("org.example.saildroid.absent315"));
  new Handler().postDelayed(()->{require(count==0,"Foreign-target broadcast reached local receiver");System.err.println("SDBROADCAST_PROBE=foreign_target_passed|local_deliveries=0");sendBroadcast(new Intent(action).setPackage(getPackageName()));new Handler().postDelayed(()->{require(count==1,"Package local broadcast was lost");sendBroadcast(new Intent(action));new Handler().postDelayed(()->{require(count==2,"Unscoped local broadcast was lost");System.err.println("SDBROADCAST_PROBE=flow_passed|foreign_deliveries=0|local_deliveries=2");v.setText("Broadcast routing passed");},500);},500);},500);
 }
 @Override protected void onDestroy(){unregisterReceiver(receiver);super.onDestroy();}
}
