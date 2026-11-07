import android.app.ActivityThread;
import android.app.Application;
import android.content.pm.ApplicationInfo;
import android.content.pm.ProviderInfo;
import android.content.res.CompatibilityInfo;
import android.os.*;
import com.android.internal.os.BinderInternal;
import java.lang.reflect.*;
import java.util.ArrayList;

/** VM-only offscreen diagnostic bootstrap of an unchanged original APK and its
 * declared Instrumentation. Application/runner/test/context remain original.
 * No window, host audio session or native app-control endpoint is provided.
 */
public final class KeystoreInstrumentationBootstrap {
    static void check(boolean yes,String reason){if(!yes)throw new IllegalStateException(reason);}
    static void set(Object object,String name,Object value)throws Exception{
        Field f=object.getClass().getDeclaredField(name);f.setAccessible(true);f.set(object,value);
    }
    public static void main(String[]args){try{
        System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root");
        String dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Matching native runtime");
        check(SdBridge.configurePrivateBinder(args[0]),"Actual private Binder");check(SdBridge.registerFrameworkNatives()==100,"Matching JNI");SdBridge.startBinderPool();
        SdCryptoProvider.install();SdTls.install();
        check(SdBridge.installClassLoaderNamespaces(),"Actual namespaces");SdClassLoaderNamespaces.installNativePathListener();check(SdBridge.installGraphicsEnvironment(),"Actual graphics configuration");
        SdServices.installAll();Looper.prepareMainLooper();
        IBinder remote=BinderInternal.getContextObject();check(remote!=null,"Actual remote software keystore");
        SdServiceManagerStub.put("android.security.keystore",remote);
        android.security.keystore.AndroidKeyStoreProvider.install();
        ApplicationInfo app=SdApkPackage.applicationInfo();check(app.uid==android.os.Process.myUid()&&app.uid==android.system.Os.getuid(),"Actual allocated APK UID");
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(app.targetSdkVersion);
        check(dalvik.system.VMRuntime.getRuntime().getTargetSdkVersion()==app.targetSdkVersion,"Real manifest target SDK");
        check(((app.flags&ApplicationInfo.FLAG_DEBUGGABLE)!=0)==dalvik.system.VMRuntime.getRuntime().isJavaDebuggable(),"Real manifest debugging policy");
        System.err.println("KEYSTORE_ORIGINAL_BOOTSTRAP=metadata|uid="+app.uid+"|target_sdk="+app.targetSdkVersion+"|debuggable="+dalvik.system.VMRuntime.getRuntime().isJavaDebuggable()+"|before_apk_classloader=true");
        android.view.ThreadedRenderer.disable(true);
        Constructor<ActivityThread> ctor=ActivityThread.class.getDeclaredConstructor();ctor.setAccessible(true);ActivityThread thread=ctor.newInstance();
        Method attach=ActivityThread.class.getDeclaredMethod("attach",boolean.class,long.class);attach.setAccessible(true);attach.invoke(thread,false,0L);
        SdServices.bindApplication(app);android.app.LoadedApk loaded=thread.getPackageInfoNoCheck(app,CompatibilityInfo.DEFAULT_COMPATIBILITY_INFO);
        SdBridge.addBionicLibraryPath(app.nativeLibraryDir);SdClassLoaderNamespaces.registerApplicationCodeCache(app);loaded.getClassLoader();
        Class<?> type=Class.forName("android.app.ActivityThread$AppBindData");Constructor<?> dc=type.getDeclaredConstructor();dc.setAccessible(true);Object data=dc.newInstance();
        set(data,"appInfo",app);set(data,"info",loaded);set(data,"processName",app.processName);set(data,"compatInfo",CompatibilityInfo.DEFAULT_COMPATIBILITY_INFO);
        set(data,"config",new android.content.res.Configuration(android.content.res.Resources.getSystem().getConfiguration()));
        ArrayList<ProviderInfo> providers=new ArrayList<>();
        for(android.content.pm.PackageParser.Provider p:SdApkPackage.parsed().providers){ProviderInfo info=new ProviderInfo(p.info);info.applicationInfo=app;info.metaData=p.metaData;providers.add(info);}
        set(data,"providers",providers);SdInstrumentation.bind(data);set(thread,"mCoreSettings",new Bundle());
        Method bind=ActivityThread.class.getDeclaredMethod("handleBindApplication",type);bind.setAccessible(true);bind.invoke(thread,data);
        Application actual=ActivityThread.currentApplication();check(actual!=null&&actual.getPackageName().equals(app.packageName)&&actual.getApplicationInfo().uid==app.uid,"Actual original APK Application");
        System.err.println("KEYSTORE_ORIGINAL_BOOTSTRAP=running|package="+app.packageName+"|actual_Application=true|declared_Instrumentation=true|offscreen_VM=true");
        Looper.loop();
    }catch(Throwable failure){while(failure.getCause()!=null)failure=failure.getCause();failure.printStackTrace();System.err.println("KEYSTORE_ORIGINAL_BOOTSTRAP=failed");System.exit(10);}}
}
