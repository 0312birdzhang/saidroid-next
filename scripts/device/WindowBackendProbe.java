import android.content.Context;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Exercise actual ViewRoot, Surface, Wayland frames and InputChannel delivery. */
public final class WindowBackendProbe {
    public static void main(String[] args)throws Exception{
        System.load(args[1]);
        if(!SdBridge.loadBionicLibrary(args[0]+"/libandroid_runtime.so",args[0]))throw new IllegalStateException("Native bootstrap failed");
        SdBridge.registerFrameworkNatives();SdServices.installAll();Looper.prepareMainLooper();
        android.app.ActivityThread thread=android.app.ActivityThread.systemMain();SdActivityHost.applyDisplayConfiguration(thread);
        java.lang.reflect.Method contextFactory=Class.forName("android.app.ContextImpl").getDeclaredMethod("createSystemContext",android.app.ActivityThread.class);contextFactory.setAccessible(true);
        Context context=(Context)contextFactory.invoke(null,thread);
        android.view.HardwareRenderer.disable(true);
        SdWindowHost.install(System.getProperty("saidroid.window.library"));SdWindowHost.start("SailDroid window validation","saildroid-window-validation");
        final LinearLayout layout=new LinearLayout(context);layout.setOrientation(LinearLayout.VERTICAL);layout.setPadding(40,100,40,40);layout.setBackgroundColor(0xff103b52);
        final TextView label=new TextView(context);label.setText("Android ViewRoot / Wayland");label.setTextColor(Color.WHITE);label.setTextSize(26);layout.addView(label);
        final Button button=new Button(context);button.setText("Touch to verify input");layout.addView(button,new LinearLayout.LayoutParams(-1,200));
        button.setOnTouchListener(new View.OnTouchListener(){@Override public boolean onTouch(View view,android.view.MotionEvent event){System.err.println("WINDOW_TOUCH=button|action="+event.getAction()+"|x="+event.getX()+"|y="+event.getY());return false;}});
        layout.setOnTouchListener(new View.OnTouchListener(){@Override public boolean onTouch(View view,android.view.MotionEvent event){System.err.println("WINDOW_TOUCH=root|action="+event.getAction()+"|x="+event.getX()+"|y="+event.getY());return false;}});
        button.setOnClickListener(new View.OnClickListener(){int count;@Override public void onClick(View view){count++;label.setText("Input handled: "+count);layout.setBackgroundColor(0xff168c66);System.err.println("WINDOW_INPUT_TEST=handled|count="+count);layout.postDelayed(new Runnable(){@Override public void run(){String output=System.getProperty("saidroid.window.snapshot");if(output!=null)try{SdSurfaceStore.saveSnapshot(output+".after.png");}catch(Exception failure){throw new IllegalStateException(failure);}}},250);}});
        WindowManager manager=(WindowManager)context.getSystemService(Context.WINDOW_SERVICE);
        WindowManager.LayoutParams attributes=new WindowManager.LayoutParams(-1,-1,WindowManager.LayoutParams.TYPE_APPLICATION,0,PixelFormat.OPAQUE);attributes.setTitle("SailDroid window validation");attributes.token=new android.os.Binder();
        manager.addView(layout,attributes);
        if(Boolean.getBoolean("saidroid.window.syntheticInput"))SdWindowSession.focus(true);
        final Handler handler=new Handler(Looper.getMainLooper());
        handler.postDelayed(new Runnable(){@Override public void run(){
            System.err.println("WINDOW_BACKEND=measured|width="+layout.getWidth()+"|height="+layout.getHeight());
            int[] position=new int[2];button.getLocationOnScreen(position);System.err.println("WINDOW_BUTTON=bounds|x="+position[0]+"|y="+position[1]+"|width="+button.getWidth()+"|height="+button.getHeight());
            String output=System.getProperty("saidroid.window.snapshot");if(output!=null)try{SdSurfaceStore.saveSnapshot(output);}catch(Exception failure){throw new IllegalStateException(failure);}
            if(Boolean.getBoolean("saidroid.window.syntheticInput")){
                long now=android.os.SystemClock.uptimeMillis()*1000000;
                SdWindowSession.input(0,0,200,300,now);SdWindowSession.input(1,0,200,300,now+50000000);
            }
        }},1500);
        handler.postDelayed(new Runnable(){@Override public void run(){
            System.err.println("WINDOW_BACKEND_TEST=complete");SdWindowHost.stop();System.exit(0);
        }},Long.getLong("saidroid.window.testDuration",8000));
        Looper.loop();
    }
}
