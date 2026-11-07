import android.os.Handler;
import android.os.Looper;
import android.os.SystemProperties;
import android.view.Choreographer;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Paths;

/** Bounded actual-ART platform consumer; deliberately no app binding or UI. */
public final class HeadlessProductProbe {
    private static final class Completed extends RuntimeException {}
    private static void need(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static boolean useVsync()throws Exception{
        Field f=Class.forName("android.view.Choreographer").getDeclaredField("USE_VSYNC");f.setAccessible(true);return f.getBoolean(null);
    }
    private static boolean property(){return SystemProperties.getBoolean("debug.choreographer.vsync",true);}
    private static void noUi()throws Exception{
        need(!SdWindowHost.isStarted(),"window host started");
        String maps=new String(Files.readAllBytes(Paths.get("/proc/self/maps")),"UTF-8");
        need(maps.contains("boot-runtime.art")&&maps.contains("boot-runtime.oat")&&maps.contains("boot-framework29-classes"),"matching actual images not mapped");
        for(String n:new String[]{"libsdwindow.so","libsdhwui","libvulkan_lvp","libvulkan_freedreno","libgallium","libGLESv2_adreno"})need(!maps.contains(n),"unexpected GPU/window mapping: "+n);
        Files.write(Paths.get("/var/tmp/smoke/maps.txt"),maps.getBytes("UTF-8"));
        for(String n:new String[]{"/dev/dri","/dev/kgsl"}){
            java.io.File[] fds=new java.io.File("/proc/self/fd").listFiles();
            if(fds!=null)for(java.io.File f:fds)need(!f.getCanonicalPath().startsWith(n),"GPU FD allocated");
        }
        need(System.getenv("SAILDROID_CONTROL_SOCKET")==null,"activation/control endpoint present");
    }
    public static void main(String[] args)throws Exception{
        final String mode=args[0];final int sdk=Integer.parseInt(args[1]);
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(sdk);
        need(dalvik.system.VMRuntime.getRuntime().getTargetSdkVersion()==sdk,"actual target SDK mismatch");
        boolean application=true,selected=mode.equals("service")||mode.equals("provider")||mode.equals("late")||mode.equals("service-provider");
        if(mode.equals("service")||mode.equals("late")||mode.equals("service-provider"))System.setProperty("saidroid.service","fixture.Service");
        if(mode.equals("provider")||mode.equals("service-provider"))System.setProperty("saidroid.provider","fixture.Provider");
        if(mode.equals("activity")||mode.equals("service-activity")){System.setProperty("saidroid.activity","fixture.Activity");if(mode.startsWith("service-"))System.setProperty("saidroid.service","fixture.Service");}
        if(mode.equals("receiver")||mode.equals("provider-receiver")){System.setProperty("saidroid.receiver","fixture.Receiver");if(mode.startsWith("provider-"))System.setProperty("saidroid.provider","fixture.Provider");}
        if(mode.equals("instrumentation")||mode.equals("service-instrumentation")){System.setProperty("saidroid.instrumentation.request","fixture.Instrumentation");if(mode.startsWith("service-"))System.setProperty("saidroid.service","fixture.Service");}
        if(mode.equals("cli")||mode.equals("broker")){application=false;if(mode.equals("broker"))System.setProperty("saidroid.service","fixture.Broker");}
        // Late-control native registration uses the real CLI prerequisites only.
        if(mode.equals("late")){
            String root=System.getenv("ANDROID_ROOT");System.load(root+"/lib/libsdbridge.so");
            need(SdBridge.loadBionicLibrary(root+"/android-libs/libandroid_runtime.so",root+"/android-libs"),"late native setup");
            need(SdBridge.registerFrameworkNatives()>0,"late native registration");need(property(),"late fresh property changed");need(useVsync(),"late setup lacks true flag");
        }
        try{SdRuntime.initializeFramework(application);need(!mode.equals("late"),"late selection unexpectedly passed");}
        catch(IllegalStateException failure){
            need(mode.equals("late")&&failure.getMessage().equals("Headless Choreographer was already initialized with vsync"),"unexpected initialization failure: "+failure);
            need(!property()&&useVsync(),"late fail-closed state differs");noUi();
            System.out.println("HEADLESS_PRODUCT=passed|mode=late|sdk="+sdk+"|fail_closed=true|before_apk=true|window=false|gpu=false");return;
        }
        need(property()!=selected&&useVsync()!=selected,"selector predicate differs");
        noUi();
        if(!selected){System.out.println("HEADLESS_PRODUCT=passed|mode="+mode+"|sdk="+sdk+"|default_vsync=true|window=false|gpu=false");return;}
        SdAudio.install();SdServices.installAll();Looper.prepareMainLooper();final Handler h=new Handler();final Choreographer first=Choreographer.getInstance();
        final int[] called={0};final long[] last={0};final boolean[] cancelled={false};
        Choreographer.FrameCallback removed=new Choreographer.FrameCallback(){public void doFrame(long t){cancelled[0]=true;}};
        first.postFrameCallback(removed);first.removeFrameCallback(removed);
        final Choreographer.FrameCallback one=new Choreographer.FrameCallback(){public void doFrame(long t){
            need(t>0&&t>=last[0]&&first.getFrameTimeNanos()==t,"callback timestamp differs");called[0]++;last[0]=t;
            Choreographer.releaseInstance();final Choreographer second=Choreographer.getInstance();need(second!=first,"instance not recreated");
            need(!property(),"lifetime property restored");
            second.postFrameCallback(new Choreographer.FrameCallback(){public void doFrame(long u){
                need(u>last[0]&&second.getFrameTimeNanos()==u,"recreated callback timestamp differs");called[0]++;last[0]=u;
                Choreographer.releaseInstance();h.postDelayed(new Runnable(){public void run(){need(!cancelled[0],"cancelled callback ran");throw new Completed();}},80);
            }});
        }};
        first.postFrameCallback(one);
        h.postDelayed(new Runnable(){public void run(){throw new AssertionError("callback deadline");}},3000);
        try{Looper.loop();throw new AssertionError("main loop unexpectedly returned");}catch(Completed expected){}
        need(called[0]==2&&!cancelled[0],"callback/cancellation counts");need(!property()&&!useVsync(),"process-lifetime selection lost");noUi();
        System.out.println("HEADLESS_PRODUCT=passed|mode="+mode+"|sdk="+sdk+"|callbacks=2|monotonic=true|frame_time_agrees=true|cancelled_callback=false|release_recreate=true|lifetime_fallback=true|window=false|gpu=false");
    }
}
