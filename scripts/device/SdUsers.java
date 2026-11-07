import android.os.*;
import android.os.Process;
import android.content.pm.UserInfo;
import java.lang.reflect.*;
import java.io.File;
import java.util.*;

/** Read-only Android user view of the actual Linux account and mounted home. */
public final class SdUsers implements InvocationHandler {
    private static final SdUsers instance=new SdUsers();private final Binder binder=new Binder();private final IUserManager service;
    private SdUsers(){service=(IUserManager)Proxy.newProxyInstance(IUserManager.class.getClassLoader(),new Class<?>[]{IUserManager.class},this);binder.attachInterface(service,"android.os.IUserManager");}
    public static IBinder binder(){return instance.binder;}
    private static int id(){return Process.myUid()/100000;}
    public static UserInfo current(){UserInfo user=new UserInfo(id(),System.getenv("USER"),UserInfo.FLAG_PRIMARY|UserInfo.FLAG_ADMIN|UserInfo.FLAG_INITIALIZED);user.serialNumber=Process.myUid();return user;}
    private static boolean unlocked(){String home=System.getenv("HOME");return home!=null&&new File(home).isDirectory()&&new File(home).canRead();}
    @Override public Object invoke(Object proxy,Method method,Object[] a){
        String n=method.getName();if(n.equals("asBinder"))return binder;if(n.equals("toString"))return "SailDroid Linux user";if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return proxy==a[0];
        if(n.equals("isUserUnlockingOrUnlocked")||n.equals("isUserUnlocked"))return (Integer)a[0]==id()&&unlocked();
        if(n.equals("isUserRunning"))return (Integer)a[0]==id();
        if(n.equals("getUserInfo"))return (Integer)a[0]==id()?current():null;
        if(n.equals("getPrimaryUser"))return current();
        if(n.equals("getUserName"))return current().name;
        if(n.equals("getUsers"))return Arrays.asList(current());
        if(n.equals("getProfiles"))return (Integer)a[0]==id()?Arrays.asList(current()):Collections.<UserInfo>emptyList();
        if(n.equals("getProfileIds"))return (Integer)a[0]==id()?new int[]{id()}:new int[0];
        if(n.equals("getProfileParent"))return null;
        if(n.equals("isManagedProfile"))return false;
        if(n.equals("getUserSerialNumber"))return (Integer)a[0]==id()?Process.myUid():-1;
        if(n.equals("getUserHandle"))return (Integer)a[0]==Process.myUid()?id():-1;
        if(n.equals("getUserRestrictions")||n.equals("getApplicationRestrictions"))return new Bundle();
        if(n.equals("hasUserRestriction")||n.equals("hasBaseUserRestriction"))return false; // No per-app management policy has been installed.
        throw new UnsupportedOperationException("Host user management: "+method.toGenericString());
    }
}
