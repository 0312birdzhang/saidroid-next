import android.net.*;
import android.os.*;
import java.io.IOException;
import java.lang.reflect.*;
public final class ProxyPermissionProbe {
    static int checks;
    static void require(boolean v,String message){checks++;if(!v)throw new AssertionError(message);}
    static final class Deny implements SdConnectivity.Permissions {
        int calls;
        public void checkAccess(){calls++;throw new SecurityException("fixture missing ACCESS_NETWORK_STATE");}
    }
    static final class NeverRead implements SdConnectivity.Provider {
        int reads;
        public SdConnectivitySnapshot read()throws IOException{reads++;throw new IOException("provider must not be consulted");}
    }
    static Object call(IConnectivityManager service,String name)throws Throwable {
        Method selected=null;
        for(Method m:IConnectivityManager.class.getMethods())if(m.getName().equals(name)){require(selected==null,"unique method "+name);selected=m;}
        require(selected!=null,"method exists "+name);
        Class<?>[] types=selected.getParameterTypes();Object[] args=new Object[types.length];
        for(int i=0;i<types.length;i++){
            if(types[i]==int.class)args[i]=Integer.valueOf(0);
            else if(types[i]==boolean.class)args[i]=Boolean.FALSE;
            else if(types[i]==long.class)args[i]=Long.valueOf(0);
        }
        if(name.equals("requestNetwork"))args[4]=Integer.valueOf(ConnectivityManager.TYPE_NONE);
        try{return selected.invoke(service,args);}catch(InvocationTargetException e){throw e.getCause();}
    }
    public static void run(boolean baseline)throws Throwable {
        Deny permission=new Deny();NeverRead provider=new NeverRead();SdConnectivity backend=new SdConnectivity(provider,permission);IConnectivityManager service=backend.serviceForFixture();int deniedProxy=0;
        try {
            for(String name:new String[]{"getGlobalProxy","getProxyForNetwork"}){
                try{require(call(service,name)==null,"no configured proxy "+name);require(!baseline,"baseline should reproduce denial "+name);}
                catch(SecurityException expected){require(baseline,"candidate unexpectedly denied startup proxy "+name);deniedProxy++;}
            }
            require(permission.calls==(baseline?2:0),"proxy permission calls");require(provider.reads==0,"proxy never observes network");
            int before=permission.calls;
            for(String name:new String[]{"getActiveNetwork","getActiveNetworkInfo","getAllNetworks","getNetworkCapabilities","getLinkProperties","isActiveNetworkMetered","listenForNetwork","requestNetwork"}){
                boolean denied=false;try{call(service,name);}catch(SecurityException expected){denied=true;}require(denied,"network observation must remain denied: "+name);
            }
            require(permission.calls-before==8,"all network operations enforce permission");require(provider.reads==0,"denial occurs before provider access");
            long[] counts=backend.countersForFixture();require(counts[0]==0&&counts[1]==0&&counts[4]==0,"no registration, poll or worker after denied calls");
            require(deniedProxy==(baseline?2:0),"baseline denial reproduced or candidate fixed");
            System.out.println("PROXY_PERMISSION=passed|variant="+(baseline?"baseline-reproduces":"candidate-fixed")+"|checks="+checks+"|network_state_checks=8|provider_reads=0|proxy_permission_calls="+(baseline?2:0));
        } finally {backend.closeForFixture();}
    }
}
