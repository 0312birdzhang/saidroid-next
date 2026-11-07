import android.content.IContentService;
import android.database.IContentObserver;
import android.net.Uri;
import android.os.Binder;
import android.os.IBinder;
import android.os.Process;
import android.os.RemoteException;
import java.lang.reflect.*;
import java.util.*;

/** Process-owned content subscriptions and corruption diagnostics.
 * No system settings, observer daemon or system-server WTF/DropBox policy. */
public final class SdContentService implements InvocationHandler {
    private static final SdContentService instance=new SdContentService();
    private final Binder binder=new Binder();
    private final IContentService service;
    private final ArrayList<Subscription> subscriptions=new ArrayList<Subscription>();
    private static final class Subscription {
        final Uri uri;final boolean descendants;final IContentObserver observer;
        Subscription(Uri uri,boolean descendants,IContentObserver observer){this.uri=uri;this.descendants=descendants;this.observer=observer;}
    }
    private SdContentService(){
        service=(IContentService)Proxy.newProxyInstance(IContentService.class.getClassLoader(),new Class<?>[]{IContentService.class},this);
        binder.attachInterface(service,"android.content.IContentService");
    }
    public static IBinder binder(){return instance.binder;}
    public static IContentService service(){return instance.service;}
    private static int ownUser(){return Process.myUid()/100000;}
    private static void checkUser(int user){if(user!=ownUser()&&user!=-2&&user!=-1)throw new SecurityException("Cross-user content subscriptions are unavailable");}
    private static boolean matches(Subscription subscription,Uri changed,int flags){
        Uri registered=subscription.uri;
        if(!Objects.equals(registered.getScheme(),changed.getScheme())||!Objects.equals(registered.getAuthority(),changed.getAuthority()))return false;
        List<String> a=registered.getPathSegments(),b=changed.getPathSegments();
        for(int i=0;i<Math.min(a.size(),b.size());i++)if(!a.get(i).equals(b.get(i)))return false;
        return a.size()>=b.size()||(subscription.descendants&&(flags&2)==0);
    }
    public static void changed(Uri uri,IContentObserver origin,boolean self,int flags)throws RemoteException{
        if(uri==null)throw new NullPointerException("uri");
        ArrayList<Subscription> snapshot;
        synchronized(instance.subscriptions){snapshot=new ArrayList<Subscription>(instance.subscriptions);}
        for(Subscription subscription:snapshot){
            boolean same=origin!=null&&subscription.observer.asBinder()==origin.asBinder();
            if((!same||self)&&matches(subscription,uri,flags))subscription.observer.onChange(same,uri,ownUser());
        }
    }
    @Override public Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
        String name=method.getName();
        if(name.equals("asBinder"))return binder;
        if(name.equals("toString"))return "SailDroid local content subscriptions";
        if(name.equals("hashCode"))return System.identityHashCode(proxy);
        if(name.equals("equals"))return proxy==args[0];
        if(name.equals("registerContentObserver")){
            checkUser((Integer)args[3]);Uri uri=(Uri)args[0];IContentObserver observer=(IContentObserver)args[2];
            if(uri==null||observer==null)throw new NullPointerException("Content subscription identity required");
            synchronized(subscriptions){subscriptions.add(new Subscription(uri,(Boolean)args[1],observer));}return null;
        }
        if(name.equals("unregisterContentObserver")){
            IBinder token=((IContentObserver)args[0]).asBinder();
            synchronized(subscriptions){for(Iterator<Subscription> it=subscriptions.iterator();it.hasNext();)if(it.next().observer.asBinder()==token)it.remove();}return null;
        }
        if(name.equals("notifyChange")){checkUser((Integer)args[4]);changed((Uri)args[0],(IContentObserver)args[1],(Boolean)args[2],(Integer)args[3]);return null;}
        if(name.equals("onDbCorruption")){
            // AOSP ContentService reports corruption; SQLite's error handler owns
            // recovery. This process-local backend has no system DropBox/WTF
            // policy. Preserve the message, stack and ASSERT severity in the
            // app's private log without recursively invoking ActivityManager.
            String tag=(String)args[0], message=(String)args[1];
            // stdout/stderr are the owning app's log even without --debug-log.
            System.err.println("SDCONTENT_CORRUPTION|priority=6|tag="+tag+"|"+message);
            System.err.println("SDCONTENT_CORRUPTION|priority=6|tag="+tag+"|at "+(String)args[2]);
            System.err.println("SDCONTENT_CORRUPTION|priority=7|tag="+tag+"|"+message);
            System.err.flush();
            return null;
        }
        if(name.equals("getSyncAdapterTypes"))return new android.content.SyncAdapterType[0];
        if(name.equals("getSyncAdapterTypesAsUser")){checkUser((Integer)args[0]);return new android.content.SyncAdapterType[0];}
        throw new UnsupportedOperationException("Content service: "+method.toGenericString());
    }
}
