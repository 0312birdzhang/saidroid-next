import android.os.*;
import java.lang.reflect.*;
import java.util.*;

/** Actual process-local Binder registry. No kernel servicemanager is contacted. */
public final class SdServiceManagerStub implements InvocationHandler {
    private static final HashMap<String,IBinder> entries=new HashMap<String,IBinder>();
    private static final SdServiceManagerStub instance=new SdServiceManagerStub();
    private final Binder binder=new Binder();private final IServiceManager service;
    private SdServiceManagerStub(){service=(IServiceManager)Proxy.newProxyInstance(IServiceManager.class.getClassLoader(),new Class<?>[]{IServiceManager.class},this);binder.attachInterface(service,"android.os.IServiceManager");}
    public static IServiceManager service(){return instance.service;}
    public static synchronized void put(String name,IBinder value){if(name==null||value==null)throw new IllegalArgumentException("Service identity required");entries.put(name,value);}
    @Override public Object invoke(Object proxy,Method method,Object[] a){
        String n=method.getName();if(n.equals("asBinder"))return binder;if(n.equals("toString"))return "SailDroid service registry";if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return proxy==a[0];
        synchronized(SdServiceManagerStub.class){
            if(n.equals("getService")||n.equals("checkService"))return entries.get((String)a[0]);
            if(n.equals("listServices"))return entries.keySet().toArray(new String[entries.size()]);
            if(n.equals("addService")){put((String)a[0],(IBinder)a[1]);return null;}
        }
        throw new UnsupportedOperationException("Local service registry: "+method.toGenericString());
    }
}
