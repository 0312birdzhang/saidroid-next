import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.content.res.CompatibilityInfo;
import android.os.*;
import android.os.Process;
import java.lang.reflect.*;
import java.util.*;

/** Actual ActivityThread Service lifecycles inside the application's process. */
public final class SdServiceHost {
    private static final Object lock=new Object();
    private static final LinkedHashMap<ComponentName,Hosted> services=new LinkedHashMap<ComponentName,Hosted>();
    private static final IdentityHashMap<IBinder,Hosted> tokens=new IdentityHashMap<IBinder,Hosted>();
    private static final IdentityHashMap<IBinder,ArrayList<Connection>> connections=new IdentityHashMap<IBinder,ArrayList<Connection>>();
    private static final class Hosted {
        final Binder token=new Binder();final ServiceInfo info;final ComponentName name;
        final long since=SystemClock.elapsedRealtime();
        final HashMap<Intent.FilterComparison,Binding> bindings=new HashMap<Intent.FilterComparison,Binding>();
        boolean created,started,closing;int startId,startResult;
        Hosted(ServiceInfo info){this.info=info;name=new ComponentName(info.packageName,info.name);}
    }
    private static final class Binding {
        final Hosted owner;final Intent intent;final ArrayList<Connection> clients=new ArrayList<Connection>();
        IBinder binder;boolean requested,published,rebind;
        Binding(Hosted owner,Intent intent){this.owner=owner;this.intent=new Intent(intent);}
    }
    private static final class Connection {
        final IServiceConnection callback;final Binding binding;volatile boolean active=true;
        Connection(IServiceConnection callback,Binding binding){this.callback=callback;this.binding=binding;}
    }
    private static void ownUser(int user){if(user!=Process.myUid()/100000)throw new SecurityException("Cross-user service access unavailable");}
    private static ServiceInfo resolve(Intent intent,String type){
        if(intent==null)throw new IllegalArgumentException("Service Intent required");
        List<ResolveInfo> candidates=SdApkPackage.resolveServices(intent,type,0);
        return candidates.isEmpty()?null:candidates.get(0).serviceInfo;
    }
    private static boolean available(ServiceInfo info){
        if(info==null)return false;
        if(info.processName!=null&&!info.processName.equals(SdApkPackage.processName())){
            System.err.println("SDSERVICE=unavailable|class="+info.name+"|reason=separate-process|process="+info.processName);return false;
        }
        return true;
    }
    private static Hosted hosted(ServiceInfo info){
        ComponentName name=new ComponentName(info.packageName,info.name);Hosted current=services.get(name);
        if(current==null||current.closing){current=new Hosted(info);services.put(name,current);tokens.put(current.token,current);}return current;
    }
    private static Hosted token(IBinder token){Hosted current=tokens.get(token);if(current==null)throw new IllegalArgumentException("Unknown Service token");return current;}
    private interface Work {void run()throws Exception;}
    private static void post(final Work work){
        Handler handler=new Handler(Looper.getMainLooper());Message message=Message.obtain(handler,new Runnable(){public void run(){try{work.run();}catch(Exception failure){System.err.println("SDSERVICE=failed|type="+failure.getClass().getName());throw new IllegalStateException("Service lifecycle failed",failure);}}});message.setAsynchronous(true);handler.sendMessage(message);
    }
    private static Object data(String name,Object...fields)throws Exception{
        Class<?> type=Class.forName("android.app.ActivityThread$"+name);Constructor<?> constructor=type.getDeclaredConstructor();constructor.setAccessible(true);Object object=constructor.newInstance();
        for(int i=0;i<fields.length;i+=2){Field field=type.getDeclaredField((String)fields[i]);field.setAccessible(true);field.set(object,fields[i+1]);}return object;
    }
    private static void invoke(String name,Object data,Class<?> type)throws Exception{
        Method method=ActivityThread.class.getDeclaredMethod(name,type);method.setAccessible(true);
        try{method.invoke(ActivityThread.currentActivityThread(),data);}catch(InvocationTargetException failure){Throwable cause=failure.getCause();if(cause instanceof Exception)throw(Exception)cause;throw new IllegalStateException(cause);}
    }
    private static void create(Hosted current,Intent intent)throws Exception{
        synchronized(lock){if(current.created)return;}
        Object data=data("CreateServiceData","token",current.token,"info",current.info,"compatInfo",CompatibilityInfo.DEFAULT_COMPATIBILITY_INFO,"intent",new Intent(intent));
        invoke("handleCreateService",data,data.getClass());synchronized(lock){current.created=true;}
        System.err.println("SDSERVICE=created|class="+current.info.name);
    }
    private static void destroyIfUnused(final Hosted current){post(new Work(){public void run()throws Exception{
        synchronized(lock){if(current.started||hasClients(current)||current.closing)return;current.closing=true;}
        destroy(current);
    }});}
    private static void destroy(Hosted current)throws Exception{
        if(current.created)invoke("handleStopService",current.token,IBinder.class);
        synchronized(lock){if(services.get(current.name)==current)services.remove(current.name);tokens.remove(current.token);current.created=false;}
        System.err.println("SDSERVICE=destroyed|class="+current.info.name);
    }
    private static boolean hasClients(Hosted current){for(Binding binding:current.bindings.values())for(Connection connection:binding.clients)if(connection.active)return true;return false;}
    public static ComponentName start(final Intent intent,String type,boolean foreground,String caller,int user){
        ownUser(user);if(!SdApkPackage.NAME.equals(caller))throw new SecurityException("Service caller mismatch");ServiceInfo info=resolve(intent,type);
        if(!available(info))return null;
        if(foreground)throw new UnsupportedOperationException("Foreground services require a host notification backend");
        final Hosted current;final int id;
        synchronized(lock){current=hosted(info);current.started=true;id=++current.startId;}
        post(new Work(){public void run()throws Exception{create(current,intent);Object data=data("ServiceArgsData","token",current.token,"startId",id,"flags",0,"args",new Intent(intent));invoke("handleServiceArgs",data,data.getClass());System.err.println("SDSERVICE=started|class="+current.info.name+"|startId="+id);}});
        return current.name;
    }
    public static int stop(Intent intent,String type,int user){
        ownUser(user);ServiceInfo info=resolve(intent,type);if(info==null)return 0;Hosted current;
        synchronized(lock){current=services.get(new ComponentName(info.packageName,info.name));if(current==null||!current.started)return 0;current.started=false;}
        destroyIfUnused(current);return 1;
    }
    public static boolean stopToken(ComponentName name,IBinder token,int startId){
        Hosted current;synchronized(lock){current=tokens.get(token);if(current==null||!current.name.equals(name)||!current.started||(startId>=0&&current.startId!=startId))return false;current.started=false;}
        destroyIfUnused(current);return true;
    }
    public static int bind(final Intent intent,String type,IServiceConnection callback,int flags,String caller,int user){
        ownUser(user);if(!SdApkPackage.NAME.equals(caller))throw new SecurityException("Service caller mismatch");if(callback==null)throw new NullPointerException("Service connection required");
        ServiceInfo info=resolve(intent,type);if(!available(info))return 0;
        final Connection connection;final Hosted current;final Binding binding;
        synchronized(lock){
            ComponentName name=new ComponentName(info.packageName,info.name);current=services.get(name);
            if(current==null&&(flags&Context.BIND_AUTO_CREATE)==0)return 0;
        }
        synchronized(lock){
            Hosted owner=hosted(info);Intent.FilterComparison key=new Intent.FilterComparison(intent);Binding item=owner.bindings.get(key);
            if(item==null){item=new Binding(owner,intent);owner.bindings.put(key,item);}binding=item;
            connection=new Connection(callback,binding);binding.clients.add(connection);IBinder token=callback.asBinder();ArrayList<Connection> group=connections.get(token);if(group==null){group=new ArrayList<Connection>();connections.put(token,group);}group.add(connection);
        }
        post(new Work(){public void run()throws Exception{
            if(!connection.active)return;Hosted owner=binding.owner;create(owner,intent);
            if(binding.published&&!binding.rebind){connection.callback.connected(owner.name,binding.binder,false);return;}
            if(binding.requested&&!binding.rebind)return;
            boolean rebind=binding.rebind;binding.requested=true;binding.rebind=false;
            Object data=data("BindServiceData","token",owner.token,"intent",new Intent(binding.intent),"rebind",rebind);invoke("handleBindService",data,data.getClass());
            if(rebind&&connection.active)connection.callback.connected(owner.name,binding.binder,false);
        }});return 1;
    }
    public static void publish(IBinder token,Intent intent,IBinder binder)throws Exception{
        ArrayList<Connection> targets;Hosted owner;
        synchronized(lock){owner=token(token);Binding binding=owner.bindings.get(new Intent.FilterComparison(intent));if(binding==null)throw new IllegalArgumentException("Unknown service binding");binding.binder=binder;binding.published=true;targets=new ArrayList<Connection>(binding.clients);}
        for(Connection connection:targets)if(connection.active)connection.callback.connected(owner.name,binder,false);
        System.err.println("SDSERVICE=bound|class="+owner.info.name+"|clients="+targets.size());
    }
    public static boolean unbind(IServiceConnection callback){
        final ArrayList<Connection> group;synchronized(lock){group=connections.remove(callback.asBinder());if(group==null)return false;for(Connection connection:group)connection.active=false;}
        post(new Work(){public void run()throws Exception{
            HashSet<Binding> affected=new HashSet<Binding>();for(Connection connection:group)affected.add(connection.binding);
            for(Binding binding:affected){boolean live=false;for(Connection connection:binding.clients)live|=connection.active;
                if(!live&&binding.requested&&binding.owner.created){Object data=data("BindServiceData","token",binding.owner.token,"intent",new Intent(binding.intent),"rebind",false);invoke("handleUnbindService",data,data.getClass());binding.requested=false;}
                destroyIfUnused(binding.owner);
            }
        }});return true;
    }
    public static void unbindFinished(IBinder token,Intent intent,boolean rebind){synchronized(lock){Hosted owner=token(token);Binding binding=owner.bindings.get(new Intent.FilterComparison(intent));if(binding!=null)binding.rebind=rebind;}}
    public static void done(IBinder token,int type,int id,int result){synchronized(lock){Hosted owner=token(token);if(type==1){owner.startResult=result;}}}
    public static IBinder peek(Intent intent,String type){ServiceInfo info=resolve(intent,type);if(info==null)return null;synchronized(lock){Hosted owner=services.get(new ComponentName(info.packageName,info.name));if(owner==null)return null;Binding binding=owner.bindings.get(new Intent.FilterComparison(intent));return binding==null?null:binding.binder;}}
    public static List<ActivityManager.RunningServiceInfo> running(int max){
        ArrayList<ActivityManager.RunningServiceInfo> result=new ArrayList<ActivityManager.RunningServiceInfo>();synchronized(lock){for(Hosted current:services.values()){if(!current.created||result.size()>=Math.max(0,max))continue;ActivityManager.RunningServiceInfo info=new ActivityManager.RunningServiceInfo();info.service=current.name;info.pid=Process.myPid();info.uid=Process.myUid();info.process=SdApkPackage.processName();info.started=current.started;info.activeSince=current.since;info.lastActivityTime=SystemClock.elapsedRealtime();for(Binding binding:current.bindings.values())for(Connection connection:binding.clients)if(connection.active)info.clientCount++;result.add(info);}}return result;
    }
    public static boolean hasLiveServices(){synchronized(lock){for(Hosted current:services.values())if(current.created&&(current.started||hasClients(current)))return true;return false;}}
    public static void closeAll()throws Exception{
        ArrayList<Hosted> snapshot;synchronized(lock){snapshot=new ArrayList<Hosted>(services.values());connections.clear();for(Hosted current:snapshot){current.started=false;current.closing=true;}}
        for(Hosted current:snapshot)destroy(current);
    }
}
