import android.os.*;
import com.android.internal.os.BinderInternal;

/** Accesses only the component's private Binder context, never the host one. */
public final class SdKernelServices {
    private static IServiceManager registry;
    public static boolean enabled(){return System.getProperty("saidroid.binder.driver")!=null;}
    public static synchronized IServiceManager registry(){
        if(!enabled())throw new IllegalStateException("Private Binder is not configured");
        if(registry==null)registry=ServiceManagerNative.asInterface(BinderInternal.getContextObject());return registry;
    }
    public static String processName(String packageName,String process){
        try{byte[] hash=java.security.MessageDigest.getInstance("SHA-256").digest(process.getBytes("UTF-8"));StringBuilder name=new StringBuilder("saidroid.process.").append(packageName).append('.');for(int i=0;i<10;i++)name.append(String.format(java.util.Locale.US,"%02x",hash[i]&255));return name.toString();}
        catch(Exception failure){throw new IllegalStateException(failure);}
    }
}
