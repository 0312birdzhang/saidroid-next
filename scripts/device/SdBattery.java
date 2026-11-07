import android.os.*;
import com.android.internal.app.IBatteryStats;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;

/** Read-only Android battery queries backed by the Linux power-supply device. */
public final class SdBattery implements InvocationHandler {
    private final Binder binder=new Binder();
    private final Object service;
    private static final SdBattery stats=new SdBattery(IBatteryStats.class,"com.android.internal.app.IBatteryStats");
    private static final SdBattery properties=new SdBattery(IBatteryPropertiesRegistrar.class,"android.os.IBatteryPropertiesRegistrar");
    private SdBattery(Class<?> type,String descriptor){service=Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},this);binder.attachInterface((IInterface)service,descriptor);}
    public static IBinder stats(){return stats.binder;}
    public static IBinder properties(){return properties.binder;}
    private static String read(String property)throws java.io.IOException{
        ArrayList<Path> candidates=new ArrayList<Path>();
        try(DirectoryStream<Path> supplies=Files.newDirectoryStream(Paths.get("/sys/class/power_supply"))){for(Path path:supplies)if("Battery".equals(new String(Files.readAllBytes(path.resolve("type")),"UTF-8").trim()))candidates.add(path);}
        if(candidates.size()!=1)throw new java.io.IOException("A unique host battery is unavailable");
        return new String(Files.readAllBytes(candidates.get(0).resolve(property)),"UTF-8").trim();
    }
    private static int status()throws java.io.IOException{
        String state=read("status");
        if("Charging".equals(state))return BatteryManager.BATTERY_STATUS_CHARGING;
        if("Discharging".equals(state))return BatteryManager.BATTERY_STATUS_DISCHARGING;
        if("Full".equals(state))return BatteryManager.BATTERY_STATUS_FULL;
        if("Not charging".equals(state))return BatteryManager.BATTERY_STATUS_NOT_CHARGING;
        return BatteryManager.BATTERY_STATUS_UNKNOWN;
    }
    @Override public Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
        String name=method.getName();
        if(name.equals("asBinder"))return binder;
        if(name.equals("toString"))return "Host battery read-only service";
        if(name.equals("hashCode"))return System.identityHashCode(proxy);
        if(name.equals("equals"))return proxy==args[0];
        if(name.equals("getProperty")){
            int id=(Integer)args[0];BatteryProperty result=(BatteryProperty)args[1];long value;
            try{
                switch(id){
                    case BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER:value=Long.parseLong(read("charge_counter"));break;
                    case BatteryManager.BATTERY_PROPERTY_CURRENT_NOW:value=Long.parseLong(read("current_now"));break;
                    case BatteryManager.BATTERY_PROPERTY_CURRENT_AVERAGE:value=Long.parseLong(read("current_avg"));break;
                    case BatteryManager.BATTERY_PROPERTY_CAPACITY:value=Long.parseLong(read("capacity"));if(value<0||value>100)throw new java.io.IOException("Host battery capacity outside range");break;
                    case BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER:value=Math.multiplyExact(Long.parseLong(read("energy_now")),1000);break;
                    case BatteryManager.BATTERY_PROPERTY_STATUS:value=status();break;
                    default:return -1;
                }
            }catch(java.io.IOException unavailable){return -1;}
            result.setLong(value);System.err.println("SDBATTERY=property|id="+id+"|source=power_supply");return 0;
        }
        if(name.equals("isCharging")){int state=status();return state==BatteryManager.BATTERY_STATUS_CHARGING||state==BatteryManager.BATTERY_STATUS_FULL;}
        if(name.equals("computeChargeTimeRemaining")||name.equals("computeBatteryTimeRemaining")){
            try{return Math.multiplyExact(Long.parseLong(read(name.equals("computeChargeTimeRemaining")?"time_to_full_now":"time_to_empty_now")),1000);}
            catch(java.io.IOException unavailable){return -1L;}
        }
        throw SdRuntimeDiagnostics.unsupported("Host battery service",method);
    }
}
