import android.app.admin.IDevicePolicyManager;
import android.os.Binder;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

/** Read-only policy for the unmanaged hosted Android user. No administrator can
 * be provisioned here. Camera grants and host device access are checked separately.
 */
public final class SdCameraPolicy implements InvocationHandler {
    private final Binder binder=new Binder();
    private final IDevicePolicyManager service;
    private SdCameraPolicy(){
        service=(IDevicePolicyManager)Proxy.newProxyInstance(IDevicePolicyManager.class.getClassLoader(),new Class<?>[]{IDevicePolicyManager.class},this);
        binder.attachInterface(service,"android.app.admin.IDevicePolicyManager");
    }
    public static void install(){SdServiceManagerStub.put("device_policy",new SdCameraPolicy().binder);}
    @Override public Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
        String name=method.getName();
        if(name.equals("asBinder"))return binder;
        if(name.equals("toString"))return "SailDroid unmanaged camera policy";
        if(name.equals("hashCode"))return System.identityHashCode(proxy);
        if(name.equals("equals"))return proxy==args[0];
        if(name.equals("getCameraDisabled")){
            if((Integer)args[1]!=android.os.Process.myUid()/100000)throw new SecurityException("Camera policy is local to the hosted user");
            System.err.println("SDCAMERA=admin_policy|disabled=false|admins=0|scope=hosted-user|permission_granted=unchanged");
            return false;
        }
        throw SdRuntimeDiagnostics.unsupported("Hosted device policy",method);
    }
}
