import org.saildroid.keystore.NativeSoftwareKeymaster;
import org.saildroid.keystore.SoftwareKeystoreService;
import java.nio.file.*;

/** Bounded VM fixture server. Root orchestrator passes the UID freshly allocated
 * from genuine original APK verification, plus the pinned private state FD. */
public final class LockAwareKeystoreServer {
    static void check(boolean ok,String why){if(!ok)throw new IllegalStateException(why);}
    public static void main(String[]args)throws Exception{
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);
        check(android.system.Os.getuid()==10050,"Actual private service UID");System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root");
        String dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Original runtime");check(SdBridge.configurePrivateBinder(args[0]),"Actual Binder");check(SdBridge.registerFrameworkNatives()==100,"Actual JNI");SdBridge.startBinderPool();
        System.load(args[1]);int uid=Integer.parseInt(args[3]);check(uid>=10000&&uid<20000&&uid!=10050,"Explicit freshly verified APK UID");
        NativeSoftwareKeymaster.initialize(Integer.parseInt(args[2]),new int[]{uid},args[4],args[5],args[6]);
        NativeSoftwareKeymaster.configureLockState(args[10]);
        check(SdBridge.becomeBinderContextManager(new SoftwareKeystoreService()),"Actual standard keystore service");
        Files.write(Paths.get(args[9]),Files.readAllBytes(Paths.get("/proc/self/maps")));
        Path ready=Paths.get(args[7]),stop=Paths.get(args[8]);Files.write(ready,("uid="+uid+"\n").getBytes("UTF-8"));long deadline=System.nanoTime()+3_900_000_000_000L;
        while(!Files.exists(stop)&&System.nanoTime()<deadline)Thread.sleep(40);
        check(Files.exists(stop),"Bounded orchestrator completion");NativeSoftwareKeymaster.close();System.out.println("STANDALONE_KEYSTORE_SERVER=ready|actual_uid=10050|original_native_closed=true|trusted_app_uid="+uid);System.out.flush();System.err.flush();System.exit(0);
    }
}
