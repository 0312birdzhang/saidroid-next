import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Arrays;

/** Platform-owned CLI startup; the requested user class retains its ordinary app loader. */
public final class SdJavaCommand {
    private SdJavaCommand() {}
    public static void main(String[] args) throws Throwable {
        if(args.length==0)throw new IllegalArgumentException("Java main class required");
        dalvik.system.VMRuntime runtime=dalvik.system.VMRuntime.getRuntime();
        runtime.setTargetSdkVersion(29);
        if(runtime.getTargetSdkVersion()!=29)throw new IllegalStateException("CLI SDK binding failed");
        System.err.println("SD_JAVA_CLI=ready|sdk=29|hidden_api=enabled|user_loader=application|ui=false");
        Class<?> target=Class.forName(args[0],true,ClassLoader.getSystemClassLoader());
        Method main=target.getMethod("main",String[].class);
        if(!Modifier.isPublic(main.getModifiers())||!Modifier.isStatic(main.getModifiers())||main.getReturnType()!=Void.TYPE)
            throw new NoSuchMethodException("main(String[]) must be public static void");
        try{main.invoke(null,(Object)Arrays.copyOfRange(args,1,args.length));}
        catch(InvocationTargetException failure){throw failure.getCause();}
    }
}
