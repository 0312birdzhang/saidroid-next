import android.hardware.input.IInputDevicesChangedListener;
import android.hardware.input.IInputManager;
import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.view.InputDevice;
import android.view.KeyCharacterMap;
import android.view.KeyEvent;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.TreeMap;

/** The two input devices actually synthesized by the Sailfish input bridge. */
public final class SdInputManager implements InvocationHandler {
    private static final SdInputManager instance=new SdInputManager();
    private final Binder binder=new Binder();
    private final IInputManager service;
    private final TreeMap<Integer,int[]> keys=new TreeMap<Integer,int[]>();
    private final ArrayList<IInputDevicesChangedListener> listeners=new ArrayList<IInputDevicesChangedListener>();
    private final InputDevice keyboard,touch;
    private SdInputManager(){
        try{
            for(int i=0;i<26;i++)key(KeyEvent.KEYCODE_A+i,'a'+i,'A'+i);
            String shifted=")!@#$%^&*(";
            for(int i=0;i<10;i++)key(KeyEvent.KEYCODE_0+i,'0'+i,shifted.charAt(i));
            key(KeyEvent.KEYCODE_SPACE,' ',' ');key(KeyEvent.KEYCODE_TAB,'\t','\t');key(KeyEvent.KEYCODE_ENTER,'\n','\n');
            int[] codes={KeyEvent.KEYCODE_COMMA,KeyEvent.KEYCODE_PERIOD,KeyEvent.KEYCODE_GRAVE,KeyEvent.KEYCODE_MINUS,KeyEvent.KEYCODE_EQUALS,KeyEvent.KEYCODE_LEFT_BRACKET,KeyEvent.KEYCODE_RIGHT_BRACKET,KeyEvent.KEYCODE_BACKSLASH,KeyEvent.KEYCODE_SEMICOLON,KeyEvent.KEYCODE_APOSTROPHE,KeyEvent.KEYCODE_SLASH};
            String normal=",.`-=[]\\;'/",upper="<>~_+{}|:\"?";
            for(int i=0;i<codes.length;i++)key(codes[i],normal.charAt(i),upper.charAt(i));
            for(int code:new int[]{KeyEvent.KEYCODE_DEL,KeyEvent.KEYCODE_FORWARD_DEL,KeyEvent.KEYCODE_DPAD_LEFT,KeyEvent.KEYCODE_DPAD_RIGHT,KeyEvent.KEYCODE_DPAD_UP,KeyEvent.KEYCODE_DPAD_DOWN,KeyEvent.KEYCODE_SHIFT_LEFT,KeyEvent.KEYCODE_SHIFT_RIGHT,KeyEvent.KEYCODE_CTRL_LEFT,KeyEvent.KEYCODE_CTRL_RIGHT,KeyEvent.KEYCODE_ALT_LEFT,KeyEvent.KEYCODE_ALT_RIGHT})key(code,0,0);
            KeyCharacterMap map=characterMap();
            Constructor<InputDevice> constructor=InputDevice.class.getDeclaredConstructor(int.class,int.class,int.class,String.class,int.class,int.class,String.class,boolean.class,int.class,int.class,KeyCharacterMap.class,boolean.class,boolean.class,boolean.class);
            constructor.setAccessible(true);
            keyboard=constructor.newInstance(-1,1,0,"Sailfish virtual keyboard",0,0,"saildroid:maliit",false,InputDevice.SOURCE_KEYBOARD,InputDevice.KEYBOARD_TYPE_ALPHABETIC,map,false,false,false);
            touch=constructor.newInstance(0,1,0,"Sailfish touch bridge",0,0,"saildroid:wayland-touch",false,InputDevice.SOURCE_TOUCHSCREEN,InputDevice.KEYBOARD_TYPE_NONE,map,false,false,false);
        }catch(Exception error){throw new ExceptionInInitializerError(error);}
        service=(IInputManager)Proxy.newProxyInstance(IInputManager.class.getClassLoader(),new Class<?>[]{IInputManager.class},this);
        binder.attachInterface(service,"android.hardware.input.IInputManager");
    }
    private void key(int code,int normal,int shift){keys.put(code,new int[]{normal,shift});}
    private static void behavior(Parcel p,int meta,int value){p.writeInt(1);p.writeInt(meta);p.writeInt(value);p.writeInt(0);p.writeInt(0);}
    private KeyCharacterMap characterMap(){
        // API29's public Parcelable creator constructs a real native KCM. The
        // wire format is KeyCharacterMap::{read,write}ToParcel in Android 10;
        // no guessed native pointer or disabled KeyEvent path is involved.
        Parcel p=Parcel.obtain();
        try{
            p.writeInt(-1);p.writeInt(KeyCharacterMap.FULL);p.writeInt(keys.size());
            for(java.util.Map.Entry<Integer,int[]> entry:keys.entrySet()){
                int normal=entry.getValue()[0],shift=entry.getValue()[1];boolean letter=normal>='a'&&normal<='z';
                p.writeInt(entry.getKey());p.writeInt(letter?shift:normal);p.writeInt(normal>='0'&&normal<='9'?normal:0);
                if(letter){behavior(p,KeyEvent.META_SHIFT_ON|KeyEvent.META_CAPS_LOCK_ON,normal);behavior(p,KeyEvent.META_CAPS_LOCK_ON,shift);}
                behavior(p,KeyEvent.META_SHIFT_ON,shift);behavior(p,0,normal);p.writeInt(0);
            }
            p.setDataPosition(0);return KeyCharacterMap.CREATOR.createFromParcel(p);
        }finally{p.recycle();}
    }
    public static IBinder binder(){return instance.binder;}
    @Override public synchronized Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
        String name=method.getName();
        if(name.equals("asBinder"))return binder;
        if(name.equals("toString"))return "Sailfish bridged input devices";
        if(name.equals("hashCode"))return System.identityHashCode(proxy);
        if(name.equals("equals"))return proxy==args[0];
        if(name.equals("getInputDeviceIds"))return new int[]{-1,0};
        if(name.equals("getInputDevice")){int id=(Integer)args[0];return id==-1?keyboard:id==0?touch:null;}
        if(name.equals("isInputDeviceEnabled")){int id=(Integer)args[0];return id==-1||id==0;}
        if(name.equals("registerInputDevicesChangedListener")){IInputDevicesChangedListener listener=(IInputDevicesChangedListener)args[0];if(listener!=null&&!listeners.contains(listener))listeners.add(listener);return null;}
        if(name.equals("hasKeys")){
            int id=(Integer)args[0],source=(Integer)args[1];int[] codes=(int[])args[2];boolean[] result=(boolean[])args[3];
            if(result.length!=codes.length)throw new IllegalArgumentException("Key result length differs");
            boolean keyboardSource=source==InputDevice.SOURCE_ANY||(source&InputDevice.SOURCE_KEYBOARD)==InputDevice.SOURCE_KEYBOARD||source==0;
            for(int i=0;i<codes.length;i++)result[i]=(id==-1)&&keyboardSource&&keys.containsKey(codes[i]);return true;
        }
        if(name.equals("isInTabletMode"))return -1;
        if(name.equals("getKeyboardLayouts")||name.equals("getKeyboardLayoutsForInputDevice"))return new android.hardware.input.KeyboardLayout[0];
        if(name.equals("getEnabledKeyboardLayoutsForInputDevice"))return new String[0];
        if(name.equals("getCurrentKeyboardLayoutForInputDevice")||name.equals("getKeyboardLayout"))return null;
        throw SdRuntimeDiagnostics.unsupported("Bridged input devices",method);
    }
}
