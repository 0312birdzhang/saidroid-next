import android.app.trust.ITrustManager;
import android.os.*;
import java.lang.reflect.*;

/** Read-only keyguard state from Sailfish MCE. Never unlocks or changes policy. */
public final class SdKeyguard implements InvocationHandler {
    private static final SdKeyguard instance=new SdKeyguard();
    private final Binder binder=new Binder();
    private final ITrustManager service;
    private SdKeyguard(){service=(ITrustManager)Proxy.newProxyInstance(ITrustManager.class.getClassLoader(),new Class<?>[]{ITrustManager.class},this);binder.attachInterface(service,"android.app.trust.ITrustManager");}
    public static IBinder binder(){return instance.binder;}
    public static boolean locked(){
        String state=SdHostState.string("get_tklock_mode");
        if(state.equals("unlocked"))return false;if(state.equals("locked")||state.startsWith("locked-"))return true;
        throw new IllegalStateException("Unknown MCE lock state: "+state);
    }

    @Override public Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
        String name=method.getName();if(name.equals("asBinder"))return binder;if(name.equals("toString"))return "Sailfish keyguard state";if(name.equals("hashCode"))return System.identityHashCode(proxy);if(name.equals("equals"))return proxy==args[0];
        if(name.equals("isDeviceLocked")){if((Integer)args[0]!=android.os.Process.myUid()/100000)throw new SecurityException("Cross-user keyguard query unavailable");return locked();}
        throw SdRuntimeDiagnostics.unsupported("Sailfish trust service",method);
    }
}
