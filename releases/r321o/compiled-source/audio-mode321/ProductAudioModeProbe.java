import android.app.*;
import android.content.*;
import android.media.*;
import android.os.*;
import java.lang.reflect.*;
import org.json.*;

/** VM platform setup and consumer only; no replacement audio service/manager/native. */
public final class ProductAudioModeProbe {
    static int checks;
    static void require(boolean value,String what){checks++;if(!value)throw new AssertionError(what);}
    static Field field(Class<?> c,String n)throws Exception{while(c!=null){try{Field f=c.getDeclaredField(n);f.setAccessible(true);return f;}catch(NoSuchFieldException e){c=c.getSuperclass();}}throw new NoSuchFieldException(n);}
    static void set(Object o,String n,Object v)throws Exception{field(o.getClass(),n).set(o,v);}
    static Object get(Object o,String n)throws Exception{return field(o.getClass(),n).get(o);}
    static final class OwnedApplication extends Application {void use(Context c){attachBaseContext(c);}@Override public Context getApplicationContext(){return this;}}
    interface ForeignGetMode {int getMode();}
    interface ArgumentGetMode {int getMode(int mode);}
    interface WrongReturnGetMode {long getMode();}
    static void reject(InvocationHandler h,IAudioService s,Method m,Object[] a)throws Throwable{try{h.invoke(s,m,a);throw new AssertionError("unrelated signature accepted: "+m);}catch(UnsupportedOperationException ok){checks++;}}
    static void read(AudioManager manager,IAudioService service,boolean baseline,String phase)throws Exception{
        if(baseline){try{manager.getMode();throw new AssertionError("baseline unexpectedly supported");}catch(UnsupportedOperationException expected){checks++;}return;}
        require(manager.getMode()==AudioManager.MODE_NORMAL,phase+": actual AudioManager getter normal");
        require(service.getMode()==AudioManager.MODE_NORMAL,phase+": actual IAudioService proxy getter normal");
    }
    public static void main(String[] args)throws Throwable{
        boolean baseline=args[0].equals("baseline");Looper.prepareMainLooper();
        // Normal production native registration, then normal production service table.
        Class.forName("SdAudio").getMethod("install").invoke(null);
        Class.forName("SdServices").getMethod("installAll").invoke(null);
        Constructor<ActivityThread> tc=ActivityThread.class.getDeclaredConstructor();tc.setAccessible(true);ActivityThread thread=tc.newInstance();Context context=thread.getSystemContext();
        OwnedApplication app=new OwnedApplication();app.use(context);set(thread,"mInitialApplication",app);set(get(context,"mPackageInfo"),"mApplication",app);
        require(context.getClass().getName().equals("android.app.ContextImpl"),"real ContextImpl");
        AudioManager manager=context.getSystemService(AudioManager.class);require(manager!=null,"real public system service manager");require(manager==context.getSystemService(Context.AUDIO_SERVICE),"real cached manager");
        IBinder binder=ServiceManager.getService(Context.AUDIO_SERVICE);IAudioService service=IAudioService.Stub.asInterface(binder);require(service!=null&&Proxy.isProxyClass(service.getClass()),"production proxy service");
        InvocationHandler handler=Proxy.getInvocationHandler(service);require(handler.getClass().getName().equals("SdAudio"),"production SdAudio invocation handler");
        require(binder==Class.forName("SdAudio").getMethod("binder").invoke(null),"ordinary registry owns actual binder");
        read(manager,service,baseline,"initial");
        int[] modes={AudioManager.MODE_CURRENT,AudioManager.MODE_INVALID,AudioManager.MODE_NORMAL,AudioManager.MODE_RINGTONE,AudioManager.MODE_IN_CALL,AudioManager.MODE_IN_COMMUNICATION,4,99,Integer.MIN_VALUE,Integer.MAX_VALUE};
        for(int mode:modes){
            try{manager.setMode(mode);throw new AssertionError("public setMode falsely accepted "+mode);}catch(UnsupportedOperationException expected){checks++;}
            read(manager,service,baseline,"after public rejected "+mode);
            try{service.setMode(mode,new Binder(),"android");throw new AssertionError("service setMode falsely accepted "+mode);}catch(UnsupportedOperationException expected){checks++;}
            read(manager,service,baseline,"after service rejected "+mode);
            try{int status=AudioSystem.setPhoneState(mode);throw new AssertionError("native setPhoneState returned "+status+" for "+mode);}catch(UnsatisfiedLinkError expected){checks++;System.out.println("AUDIO_MODE_NATIVE=rejected|mode="+mode+"|type=UnsatisfiedLinkError");}
            read(manager,service,baseline,"after rejected native "+mode);
        }
        try{service.isSpeakerphoneOn();throw new AssertionError("unknown method accepted");}catch(UnsupportedOperationException expected){checks++;}
        reject(handler,service,ForeignGetMode.class.getDeclaredMethod("getMode"),null);
        reject(handler,service,ArgumentGetMode.class.getDeclaredMethod("getMode",int.class),new Object[]{0});
        reject(handler,service,WrongReturnGetMode.class.getDeclaredMethod("getMode"),null);
        // Existing safe branches require no host PulseAudio/profile mutation.
        require(service.getStreamMinVolume(AudioManager.STREAM_MUSIC)==0,"old min volume retained");require(service.getStreamMaxVolume(AudioManager.STREAM_MUSIC)==100,"old max volume retained");
        require(service.asBinder()==binder,"old asBinder retained");
        Class<?> audio=Class.forName("SdAudio");Method sco=audio.getMethod("bluetoothScoRoute",JSONObject.class);
        require(!(Boolean)sco.invoke(null,new JSONObject("{\"device_api\":\"alsa\",\"bluetooth_protocol\":\"sco\",\"bluez5_profile\":\"hfp_hf\"}")),"old non-Bluetooth route false");
        require((Boolean)sco.invoke(null,new JSONObject("{\"device_api\":\"bluez5\",\"bluetooth_protocol\":\"sco\",\"bluez5_profile\":\"hfp_hf\"}")),"old SCO recognition retained");
        for(int n=0;n<8;n++)read(manager,service,baseline,"repeat "+n);
        String mappings=new String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get("/proc/self/maps")),"UTF-8");require(mappings.contains("boot-runtime.art")&&mappings.contains("boot-runtime.oat"),"real runtime boot image mappings");
        System.out.println("AUDIO_MODE_PRODUCT=passed|variant="+args[0]+"|checks="+checks+"|pid="+android.os.Process.myPid()+"|publicManager=true|productionDispatch=true|nativeRegistration=true|baselineUnsupported="+baseline+"|supportedTransitions=none|hostCallMode=unintegrated|phone=false");
    }
}
