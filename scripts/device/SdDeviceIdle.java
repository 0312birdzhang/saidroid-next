import android.os.*;
import java.lang.reflect.*;
import java.util.*;

/** Queries the runtime's power exemption inventory, independent of host MCE policy. */
public final class SdDeviceIdle implements InvocationHandler {
    private static final SdDeviceIdle INSTANCE=new SdDeviceIdle();
    private final Binder binder=new Binder();
    private final IDeviceIdleController service;
    // No exemption configuration is provisioned by this standalone runtime.
    // Host power-save state is separately exposed by SdPower; it is not an app exemption.
    private final Set<String> exemptions=Collections.emptySet();
    private SdDeviceIdle(){service=(IDeviceIdleController)Proxy.newProxyInstance(IDeviceIdleController.class.getClassLoader(),new Class<?>[]{IDeviceIdleController.class},this);binder.attachInterface(service,"android.os.IDeviceIdleController");}
    public static IBinder binder(){return INSTANCE.binder;}
    @Override public Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
        String name=method.getName();
        if(name.equals("asBinder"))return binder;
        if(name.equals("toString"))return "SailDroid power exemption inventory";
        if(name.equals("hashCode"))return System.identityHashCode(proxy);
        if(name.equals("equals"))return proxy==args[0];
        if(name.equals("isPowerSaveWhitelistApp")||name.equals("isPowerSaveWhitelistExceptIdleApp"))return exemptions.contains(Objects.requireNonNull((String)args[0],"packageName"));
        throw SdRuntimeDiagnostics.unsupported("Runtime device idle policy",method);
    }
}
