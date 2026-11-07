import java.util.*;
/** API 29 graphics configuration for the selected host Wayland renderer. */
public final class SdGraphicsEnvironment {
    private static final WeakHashMap<ClassLoader,String> layerPaths=new WeakHashMap<ClassLoader,String>();
    private static String debugLayers="",debugLayersGles="";
    private static String requestedDriver,requestedVersion,packageName;
    private static long requestedVersionCode,requestedBuildTime,lastLaunchHint;
    public static int canLoadSystemLibraries(){return 0; /* No Android SPHAL linker namespace. */}
    public static synchronized void layers(ClassLoader loader,String paths){if(loader==null)throw new IllegalArgumentException("Graphics ClassLoader required");layerPaths.put(loader,paths==null?"":paths);}
    public static synchronized void debug(String layers,boolean gles){if(layers!=null&&!layers.isEmpty())throw new UnsupportedOperationException("Android GPU debug layer namespaces are not configured");if(gles)debugLayersGles="";else debugLayers="";}
    public static synchronized void stats(String driver,String version,long code,long time,String app,int vulkan){
        if(vulkan!=0)throw new UnsupportedOperationException("Vulkan rendering is not provided by this GLES window backend");
        requestedDriver=driver;requestedVersion=version;requestedVersionCode=code;requestedBuildTime=time;packageName=app;
        System.err.println("SDGRAPHICS=configured|renderer="+(SdWindowHost.hardware()?"hwui-gles-wayland":"software-wayland")+"|package="+app);
    }
    public static synchronized void driver(String path,String sphal){throw new UnsupportedOperationException("External GPU drivers are not configured for this renderer");}
    public static boolean angle(String app){return false; /* No ANGLE renderer was configured. */}
    public static synchronized void hint(){lastLaunchHint=System.nanoTime();if(SdWindowHost.isStarted())SdWindowHost.requestFrame();}
}
