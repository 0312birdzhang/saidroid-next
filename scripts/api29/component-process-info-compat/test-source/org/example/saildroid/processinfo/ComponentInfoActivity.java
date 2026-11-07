package org.example.saildroid.processinfo;
import android.app.Activity;import android.app.Service;import android.os.Bundle;import android.os.IBinder;import android.content.*;import android.content.pm.*;import android.database.Cursor;import android.net.Uri;
public class ComponentInfoActivity extends Activity {
 public static class Remote extends Activity {}
 public static class LocalService extends Service {public IBinder onBind(Intent i){return null;}}
 public static class RemoteService extends LocalService {}
 public static class LocalProvider extends ContentProvider {
  public boolean onCreate(){return true;}public Cursor query(Uri u,String[]p,String s,String[]a,String o){return null;}public String getType(Uri u){return null;}public Uri insert(Uri u,ContentValues v){return null;}public int delete(Uri u,String s,String[]a){return 0;}public int update(Uri u,ContentValues v,String s,String[]a){return 0;}
 }
 public static class RemoteProvider extends LocalProvider {}
 private void verify(ComponentInfo info){String expected=getPackageName()+(info.name.contains("Remote")?":worker":"");if(!expected.equals(info.processName))throw new AssertionError(info.name+" process="+info.processName+" expected="+expected);if(info.applicationInfo==null||!getPackageName().equals(info.applicationInfo.processName))throw new AssertionError("application default process");}
 @Override public void onCreate(Bundle state){super.onCreate(state);try{
  PackageManager pm=getPackageManager();String pkg=getPackageName();PackageInfo p=pm.getPackageInfo(pkg,PackageManager.GET_ACTIVITIES|PackageManager.GET_SERVICES|PackageManager.GET_PROVIDERS);
  for(ActivityInfo i:p.activities){System.err.println("COMPONENT_PROCESS_ACTIVITY="+i.name);verify(i);verify(pm.getActivityInfo(new ComponentName(pkg,i.name),0));}
  for(ServiceInfo i:p.services){verify(i);verify(pm.getServiceInfo(new ComponentName(pkg,i.name),0));}
  for(ProviderInfo i:p.providers){verify(i);verify(pm.getProviderInfo(new ComponentName(pkg,i.name),0));}
  java.util.Set<String> names=new java.util.HashSet<>();for(ActivityInfo i:p.activities)names.add(i.name);java.util.Set<String> expectedNames=new java.util.HashSet<>(java.util.Arrays.asList(ComponentInfoActivity.class.getName(),Remote.class.getName(),"android.app.AppDetailsActivity"));if(!names.equals(expectedNames))throw new AssertionError("activity names="+names);
  int services=0,activities=0;for(ResolveInfo i:pm.queryIntentServices(new Intent("org.example.PROCESSINFO").setPackage(pkg),0)){verify(i.serviceInfo);services++;}for(ResolveInfo i:pm.queryIntentActivities(new Intent("org.example.PROCESSINFO").setPackage(pkg),0)){verify(i.activityInfo);activities++;}
  if(p.activities.length!=3||p.services.length!=2||p.providers.length!=2||services!=2||activities!=1)throw new AssertionError("component/query counts: activities="+p.activities.length+", services="+p.services.length+", providers="+p.providers.length+", queriedServices="+services+", queriedActivities="+activities);
  System.err.println("COMPONENT_PROCESS_FIXTURE=PASS|inherited-and-explicit=true|activity-service-provider=true|direct-package-query=true");
 }catch(Throwable e){System.err.println("COMPONENT_PROCESS_FIXTURE=FAIL|"+e);e.printStackTrace();}}
}
