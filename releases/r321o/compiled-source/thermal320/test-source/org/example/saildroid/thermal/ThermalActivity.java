package org.example.saildroid.thermal;
import android.app.Activity;
import android.os.Bundle;
import android.os.PowerManager;
import android.widget.TextView;
import java.util.concurrent.atomic.AtomicInteger;

/** Ordinary application domain: uses the unmodified public Android API only. */
public final class ThermalActivity extends Activity {
 @Override public void onCreate(Bundle state) {
  super.onCreate(state);
  try {
   PowerManager manager=(PowerManager)getSystemService(POWER_SERVICE);
   if(manager==null)throw new AssertionError("power manager missing");
   int status=manager.getCurrentThermalStatus();
   if(status<0||status>6)throw new AssertionError("invalid status");
   AtomicInteger count=new AtomicInteger(), observed=new AtomicInteger(-1);
   PowerManager.OnThermalStatusChangedListener listener=value->{count.incrementAndGet();observed.set(value);};
   manager.addThermalStatusListener(Runnable::run,listener);
   if(count.get()!=1||observed.get()!=status)throw new AssertionError("initial callback differs");
   boolean duplicateRejected=false;
   try{manager.addThermalStatusListener(Runnable::run,listener);}catch(IllegalArgumentException expected){duplicateRejected=true;}
   if(!duplicateRejected)throw new AssertionError("duplicate listener accepted");
   manager.removeThermalStatusListener(listener);
   boolean unknownRejected=false;
   try{manager.removeThermalStatusListener(listener);}catch(IllegalArgumentException expected){unknownRejected=true;}
   if(!unknownRejected)throw new AssertionError("unknown listener removal accepted");
   if(manager.getCurrentThermalStatus()!=status)throw new AssertionError("query changed during fixture");
   TextView view=new TextView(this);view.setText("Private thermal API contract");setContentView(view);
   System.out.println("THERMAL_FIXTURE=PASS|status="+status+"|callbacks="+count.get()+"|duplicate=rejected|removed=true|hidden_api=enabled");
  }catch(Throwable failure){System.out.println("THERMAL_FIXTURE=FAIL|"+failure);failure.printStackTrace();}
 }
}
