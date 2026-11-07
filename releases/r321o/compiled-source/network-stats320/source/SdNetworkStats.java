import android.net.INetworkStatsService;
import android.os.Binder;
import android.os.IBinder;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;

/** Read-only Linux interface counters. No invented per-application accounting. */
public final class SdNetworkStats implements InvocationHandler {
    private static final SdNetworkStats INSTANCE = new SdNetworkStats(new File("/proc/net/dev"), new File("/sys/class/net"));
    private final File counters, links;
    private final Binder binder = new Binder();
    private final INetworkStatsService service;
    SdNetworkStats(File counters, File links) {
        this.counters = counters; this.links = links;
        service = (INetworkStatsService) Proxy.newProxyInstance(INetworkStatsService.class.getClassLoader(), new Class<?>[]{INetworkStatsService.class}, this);
        binder.attachInterface(service, "android.net.INetworkStatsService");
    }
    public static IBinder binder() { return INSTANCE.binder; }
    private Map<String,long[]> snapshot() throws IOException {
        Map<String,long[]> result = new TreeMap<>();
        try (BufferedReader in = new BufferedReader(new FileReader(counters))) {
            String line;
            while ((line=in.readLine()) != null) {
                int colon=line.indexOf(':'); if(colon<0) continue;
                String name=line.substring(0,colon).trim();
                String[] values=line.substring(colon+1).trim().split("\\s+");
                if(values.length != 16) throw new IOException("Malformed interface counters");
                long[] row=new long[4];
                try { row[0]=Long.parseLong(values[0]);row[1]=Long.parseLong(values[1]);row[2]=Long.parseLong(values[8]);row[3]=Long.parseLong(values[9]); }
                catch(NumberFormatException e) { throw new IOException("Invalid interface counter",e); }
                for(long value:row) if(value<0) throw new IOException("Interface counter overflow");
                result.put(name,row);
            }
        }
        if(result.isEmpty()) throw new IOException("Host interface counters unavailable");
        return result;
    }
    private String[] mobile(Map<String,long[]> rows) throws IOException {
        List<String> result=new ArrayList<>();
        for(String name:rows.keySet()) {
            // Logical modem data links, not their aggregate rmnet_ipa parent or
            // reverse tether/offload links (which would count traffic twice).
            if(!name.matches("(?:rmnet_data[0-9]+|rmnet[0-9]+|wwan[0-9]+)")) continue;
            try(BufferedReader in=new BufferedReader(new FileReader(new File(new File(links,name),"type")))) {
                String type=in.readLine();
                // Qualcomm pre-4.14 kernels use 530 for ARPHRD_RAWIP; mainline uses 519.
                if("519".equals(type)||"530".equals(type)) result.add(name);
                else throw new IOException("Unsupported modem link type: "+type);
            }
        }
        return result.toArray(new String[0]);
    }
    private static long counter(long[] row,int type) {
        return row==null||type<0||type>=4 ? -1L : row[type];
    }
    @Override public Object invoke(Object proxy,Method method,Object[] args) throws Throwable {
        String name=method.getName();
        if(name.equals("asBinder"))return binder;
        if(name.equals("toString"))return "Sailfish Linux interface statistics";
        if(name.equals("hashCode"))return System.identityHashCode(proxy);
        if(name.equals("equals"))return proxy==args[0];
        if(name.equals("getUidStats"))return -1L; // Shared host UID cannot identify an Android application's traffic.
        if(name.equals("getMobileIfaces"))return mobile(snapshot());
        if(name.equals("getIfaceStats"))return counter(snapshot().get((String)args[0]),(Integer)args[1]);
        if(name.equals("getTotalStats")) {
            int type=(Integer)args[0];if(type<0||type>=4)return -1L;
            long total=0;
            for(Map.Entry<String,long[]> row:snapshot().entrySet()) {
                if(row.getKey().equals("lo"))continue;
                total=Math.addExact(total,counter(row.getValue(),type));
            }
            return total;
        }
        throw SdRuntimeDiagnostics.unsupported("Host network statistics",method);
    }
}
