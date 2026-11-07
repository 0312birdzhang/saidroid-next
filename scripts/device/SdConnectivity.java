import android.net.*;
import android.os.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;

/** Read-only view of host Linux links and routes. Never changes Sailfish networking. */
public final class SdConnectivity implements InvocationHandler {
    private static final SdConnectivity INSTANCE=new SdConnectivity();
    private final Binder binder=new Binder();
    private final IConnectivityManager service;
    private SdConnectivity(){service=(IConnectivityManager)java.lang.reflect.Proxy.newProxyInstance(IConnectivityManager.class.getClassLoader(),new Class<?>[]{IConnectivityManager.class},this);binder.attachInterface(service,"android.net.IConnectivityManager");}
    public static IBinder binder(){return INSTANCE.binder;}
    private static final class Link {
        java.net.NetworkInterface iface;int type;boolean defaultRoute;
        Network network(){return new Network(iface.getIndex());}
        NetworkInfo info(){NetworkInfo result=new NetworkInfo(type,0,type==ConnectivityManager.TYPE_WIFI?"WIFI":type==ConnectivityManager.TYPE_MOBILE?"MOBILE":"ETHERNET","");result.setIsAvailable(true);result.setDetailedState(NetworkInfo.DetailedState.CONNECTED,null,iface.getName());return result;}
        LinkProperties properties(){LinkProperties value=new LinkProperties();value.setInterfaceName(iface.getName());for(java.net.InterfaceAddress address:iface.getInterfaceAddresses())if(address.getAddress()!=null)value.addLinkAddress(new LinkAddress(address.getAddress(),address.getNetworkPrefixLength()));return value;}
        NetworkCapabilities capabilities(){NetworkCapabilities value=new NetworkCapabilities();value.addTransportType(type==ConnectivityManager.TYPE_WIFI?NetworkCapabilities.TRANSPORT_WIFI:type==ConnectivityManager.TYPE_MOBILE?NetworkCapabilities.TRANSPORT_CELLULAR:NetworkCapabilities.TRANSPORT_ETHERNET);value.addCapability(NetworkCapabilities.NET_CAPABILITY_NOT_RESTRICTED);if(defaultRoute)value.addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);if(type!=ConnectivityManager.TYPE_MOBILE)value.addCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED);return value;}
    }
    private static List<Link> links()throws IOException{
        Set<String> defaults=new HashSet<String>();
        try(BufferedReader input=new BufferedReader(new FileReader("/proc/net/route"))){String line;while((line=input.readLine())!=null){String[] f=line.trim().split("\\s+");if(f.length>=4&&f[1].equals("00000000")&&(Integer.parseInt(f[3],16)&1)!=0)defaults.add(f[0]);}}
        List<Link> result=new ArrayList<Link>();Enumeration<java.net.NetworkInterface> all=java.net.NetworkInterface.getNetworkInterfaces();
        if(all!=null)while(all.hasMoreElements()){java.net.NetworkInterface iface=all.nextElement();if(!iface.isUp()||iface.isLoopback()||!iface.getInetAddresses().hasMoreElements())continue;Link link=new Link();link.iface=iface;String name=iface.getName();link.type=name.startsWith("wlan")||name.startsWith("wl")?ConnectivityManager.TYPE_WIFI:name.startsWith("rmnet")||name.startsWith("wwan")?ConnectivityManager.TYPE_MOBILE:ConnectivityManager.TYPE_ETHERNET;link.defaultRoute=defaults.contains(name);result.add(link);}
        return result;
    }
    private static Link active(List<Link> links){for(Link link:links)if(link.defaultRoute)return link;return null;}
    @Override public Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
        String name=method.getName();if(name.equals("asBinder"))return binder;if(name.equals("toString"))return "SailDroid host connectivity";if(name.equals("hashCode"))return System.identityHashCode(proxy);if(name.equals("equals"))return proxy==args[0];
        if(name.equals("isNetworkSupported")){int type=(Integer)args[0];return type==ConnectivityManager.TYPE_WIFI||type==ConnectivityManager.TYPE_MOBILE||type==ConnectivityManager.TYPE_ETHERNET;}
        List<Link> links=links();Link selected=active(links);
        if(name.equals("getNetworkInfoForUid")){
            if((Integer)args[1]!=android.os.Process.myUid())throw new SecurityException("Cross-user network query unavailable");
            for(Link link:links)if(link.network().equals(args[0]))return link.info();return null;
        }
        if(name.equals("getActiveNetwork"))return selected==null?null:selected.network();
        if(name.equals("getActiveNetworkInfo")||name.equals("getActiveNetworkInfoForUid"))return selected==null?null:selected.info();
        if(name.equals("getActiveLinkProperties"))return selected==null?null:selected.properties();
        if(name.equals("isActiveNetworkMetered"))return selected==null||selected.type==ConnectivityManager.TYPE_MOBILE;
        if(name.equals("getAllNetworks")){Network[] result=new Network[links.size()];for(int i=0;i<links.size();i++)result[i]=links.get(i).network();return result;}
        if(name.equals("getAllNetworkInfo")){NetworkInfo[] result=new NetworkInfo[links.size()];for(int i=0;i<links.size();i++)result[i]=links.get(i).info();return result;}
        if(name.equals("getNetworkInfo")||name.equals("getNetworkForType")||name.equals("getLinkPropertiesForType")){
            for(Link link:links)if(link.type==(Integer)args[0])return name.equals("getNetworkInfo")?link.info():name.equals("getNetworkForType")?link.network():link.properties();return null;
        }
        if(name.equals("getNetworkInfoForNetwork")||name.equals("getLinkProperties")||name.equals("getNetworkCapabilities")){
            for(Link link:links)if(link.network().equals(args[0]))return name.equals("getNetworkInfoForNetwork")?link.info():name.equals("getLinkProperties")?link.properties():link.capabilities();return null;
        }
        if(name.equals("getGlobalProxy")||name.equals("getProxyForNetwork"))return null; // No proxy configured by this runtime.
        if(name.equals("isTetheringSupported"))return false;
        throw SdRuntimeDiagnostics.unsupported("Host connectivity",method);
    }
}
