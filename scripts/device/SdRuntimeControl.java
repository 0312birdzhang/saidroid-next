import android.os.*;

/** Native authenticated close endpoint for a process without a Wayland window. */
public final class SdRuntimeControl {
    private static Handler main;
    private static native void nativeStart(String path);
    private static native void nativeStop();
    public static void start(){main=new Handler(Looper.getMainLooper());String path=System.getenv("SAILDROID_CONTROL_SOCKET");if(path==null)throw new IllegalStateException("Runtime control path missing");nativeStart(path);}
    public static void stop(){if(main!=null){nativeStop();main=null;}}
    private static void onCloseRequested(){Message message=Message.obtain(main,new Runnable(){public void run(){try{SdServiceHost.closeAll();}catch(Exception failure){failure.printStackTrace();}finally{System.err.println("SDRUNTIME=closed|role=headless");System.exit(0);}}});message.setAsynchronous(true);main.sendMessage(message);}
}
