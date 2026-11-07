import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Arrays;

/** Headless platform bootstrap for ordinary application-owned Java command classes. */
public final class SdJavaCommand {
    private SdJavaCommand() {}
    public static void main(String[] args) throws Throwable {
        if(args.length==0)throw new IllegalArgumentException("Java main class required");
        dalvik.system.VMRuntime runtime=dalvik.system.VMRuntime.getRuntime();
        runtime.setTargetSdkVersion(29);
        if(runtime.getTargetSdkVersion()!=29)throw new IllegalStateException("CLI SDK binding failed");
        ClassLoader loader=ClassLoader.getSystemClassLoader();
        if(loader==Object.class.getClassLoader())throw new SecurityException("CLI application loader unavailable");
        // Check ownership without running the requested class initializer. A
        // platform-owned bootstrap must not expose other boot-owned main methods.
        Class<?> target=Class.forName(args[0],false,loader);
        if(target.getClassLoader()!=loader)throw new SecurityException("Java main class must belong to the application loader");
        Method main=target.getMethod("main",String[].class);
        if(main.getDeclaringClass().getClassLoader()!=loader)
            throw new SecurityException("Java main method must belong to the application loader");
        if(!Modifier.isPublic(main.getModifiers())||!Modifier.isStatic(main.getModifiers())||main.getReturnType()!=Void.TYPE)
            throw new NoSuchMethodException("main(String[]) must be public static void");
        // Reuse the actual component's headless native/framework initialization.
        // No APK/Application, service manager, audio session or window is started.
        SdRuntime.initializeFramework(false);
        if(!SdBridge.installClassLoaderNamespaces())throw new IllegalStateException("CLI native namespace backend unavailable");
        SdClassLoaderNamespaces.installNativePathListener();
        System.err.println("SD_JAVA_CLI=ready|sdk=29|hidden_api=enabled|user_loader=application|ui=false");
        System.err.println("SD_JAVA_CLI=framework|mode=headless|native=component-private|ui=false");
        try{main.invoke(null,(Object)Arrays.copyOfRange(args,1,args.length));}
        catch(InvocationTargetException failure){throw failure.getCause();}
    }
}
