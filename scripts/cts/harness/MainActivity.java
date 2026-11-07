package org.example.saildroid.ctsharness;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import dalvik.system.DexClassLoader;
import java.lang.reflect.*;
import org.json.*;
import java.io.*;

/** Diagnostic adapter only. Executes unmodified official APK JUnit classes.
 * It is NOT the CTS instrumentation/Tradefed runner and cannot certify CTS.
 */
public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle state){
        super.onCreate(state);TextView status=new TextView(this);status.setText("Official API29 test diagnostics");setContentView(status);
        new Thread(new Runnable(){public void run(){execute();}},"official-api29-tests").start();
    }
    private void injectContext(Object test,ClassLoader loader)throws Exception{
        Class<?> suite=loader.loadClass("junit.framework.TestSuite");
        if(suite.isInstance(test)){
            java.util.Enumeration<?> children=(java.util.Enumeration<?>)suite.getMethod("tests").invoke(test);
            while(children.hasMoreElements())injectContext(children.nextElement(),loader);
        }else if(test instanceof android.test.AndroidTestCase){
            ((android.test.AndroidTestCase)test).setContext(getApplicationContext());
        }
    }
    private void execute(){
        JSONObject summary=new JSONObject();JSONArray classes=new JSONArray();
        try{
            File plan=new File(getFilesDir(),"plan.json");
            JSONObject config=new JSONObject(new String(java.nio.file.Files.readAllBytes(plan.toPath()),"UTF-8"));
            String apk=config.getString("apk");
            DexClassLoader loader=new DexClassLoader(apk,getCodeCacheDir().getPath(),null,getClassLoader());
            // The actual ActivityThread Instrumentation, not a fabricated target.
            Class<?> thread=Class.forName("android.app.ActivityThread");Object current=thread.getMethod("currentActivityThread").invoke(null);
            Object instrumentation=thread.getMethod("getInstrumentation").invoke(current);
            for(String name:new String[]{"androidx.test.platform.app.InstrumentationRegistry","androidx.test.InstrumentationRegistry"})try{
                Class<?> registry=loader.loadClass(name);registry.getMethod("registerInstance",android.app.Instrumentation.class,Bundle.class).invoke(null,instrumentation,new Bundle());
            }catch(ClassNotFoundException absent){}
            // AndroidJUnit4 defaults to Robolectric when java.vm.name is not
            // "Dalvik". Our native ART reports its actual name; select the
            // bundled Android delegate through its supported runner setting.
            System.setProperty("android.junit.runner","androidx.test.internal.runner.junit4.AndroidJUnit4ClassRunner");
            Class<?> core=loader.loadClass("org.junit.runner.JUnitCore");
            Method run=core.getMethod("runClasses",Class[].class);int runs=0,failures=0,ignored=0;
            JSONArray names=config.getJSONArray("classes");
            for(int i=0;i<names.length();i++){
                String name=names.getString(i);JSONObject row=new JSONObject();row.put("class",name);
                try{
                    Class<?> test=loader.loadClass(name);Object result;
                    Class<?> testCase=loader.loadClass("junit.framework.TestCase");
                    if(testCase.isAssignableFrom(test)){
                        Class<?> suiteType=loader.loadClass("junit.framework.TestSuite"),testType=loader.loadClass("junit.framework.Test");
                        Object suite=suiteType.getConstructor(Class.class).newInstance(test);
                        injectContext(suite,loader);
                        Class<?> adapter=loader.loadClass("org.junit.internal.runners.JUnit38ClassRunner");
                        Object runner=adapter.getConstructor(testType).newInstance(suite);
                        result=core.getMethod("run",loader.loadClass("org.junit.runner.Runner")).invoke(core.newInstance(),runner);
                    }else result=run.invoke(null,(Object)new Class<?>[]{test});
                    Class<?> rt=result.getClass();
                    int count=(Integer)rt.getMethod("getRunCount").invoke(result),failed=(Integer)rt.getMethod("getFailureCount").invoke(result),skip=(Integer)rt.getMethod("getIgnoreCount").invoke(result);
                    row.put("run",count);row.put("failures",failed);row.put("ignored",skip);runs+=count;failures+=failed;ignored+=skip;
                    JSONArray details=new JSONArray();
                    for(Object f:(Iterable<?>)rt.getMethod("getFailures").invoke(result)){
                        Class<?> ft=f.getClass();JSONObject detail=new JSONObject();detail.put("test",ft.getMethod("getTestHeader").invoke(f));detail.put("trace",ft.getMethod("getTrace").invoke(f));details.put(detail);
                    }
                    row.put("details",details);System.err.println("SDCTS=class|name="+name+"|run="+count+"|failed="+failed+"|ignored="+skip);
                }catch(Throwable problem){while(problem.getCause()!=null)problem=problem.getCause();row.put("blocked",problem.toString());System.err.println("SDCTS=blocked|name="+name+"|type="+problem.getClass().getName());}
                classes.put(row);
            }
            summary.put("adapter","direct-junit-diagnostic-not-cts-certification");summary.put("apk",apk);summary.put("classes",classes);summary.put("run",runs);summary.put("failures",failures);summary.put("ignored",ignored);
            System.err.println("SDCTS=complete|run="+runs+"|failed="+failures+"|ignored="+ignored+"|classes="+classes.length());
        }catch(Throwable failure){try{summary.put("blocked",failure.toString());}catch(Exception ignored){}failure.printStackTrace();System.err.println("SDCTS=blocked|type="+failure.getClass().getName());}
        try{File out=new File(getFilesDir(),"result.json"),pending=new File(getFilesDir(),"result.pending");try(FileOutputStream stream=new FileOutputStream(pending)){stream.write(summary.toString(2).getBytes("UTF-8"));stream.getFD().sync();}if(!pending.renameTo(out))throw new IOException("Cannot publish completed result");}catch(Exception failure){throw new IllegalStateException(failure);}
    }
}
