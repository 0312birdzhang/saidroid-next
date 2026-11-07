package org.example.saildroid.netstats;
import android.app.Activity;
import android.os.Bundle;
import android.net.TrafficStats;
import android.widget.TextView;
public final class NetworkStatsActivity extends Activity {
 @Override public void onCreate(Bundle b){super.onCreate(b);try{
  android.os.PowerManager power=(android.os.PowerManager)getSystemService(POWER_SERVICE);
  if(power.isIgnoringBatteryOptimizations(getPackageName())||power.isIgnoringBatteryOptimizations("org.example.notinstalled"))throw new AssertionError("Unexpected power exemption");
  System.out.println("DEVICE_IDLE_FIXTURE=PASS|own=false|uninstalled=false|host-policy-unchanged=true");
  long rx=TrafficStats.getMobileRxBytes(),tx=TrafficStats.getMobileTxBytes(),rp=TrafficStats.getMobileRxPackets(),tp=TrafficStats.getMobileTxPackets();
  long totalRx=TrafficStats.getTotalRxBytes(),totalTx=TrafficStats.getTotalTxBytes(),uid=TrafficStats.getUidRxBytes(android.os.Process.myUid());
  if(rx<0||tx<0||rp<0||tp<0||totalRx<rx||totalTx<tx||uid!=-1)throw new AssertionError("Invalid or invented counters");
  String result="NETWORK_STATS_FIXTURE=PASS|rx="+rx+"|tx="+tx+"|rxPackets="+rp+"|txPackets="+tp+"|totalRx="+totalRx+"|totalTx="+totalTx+"|uid="+uid;
  System.out.println(result);TextView v=new TextView(this);v.setText(result);setContentView(v);
 }catch(Throwable e){System.out.println("NETWORK_STATS_FIXTURE=FAIL|"+e);e.printStackTrace();}}
}
