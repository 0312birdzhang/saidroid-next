package org.example.saildroid.audio;
import android.app.Activity;
import android.media.AudioManager;
import android.os.*;
import android.widget.TextView;
import org.json.JSONObject;
import java.io.FileOutputStream;

/** Query from a real HandlerThread, as QQ's conversation PTT initialization does. */
public final class MainActivity extends Activity {
    private HandlerThread thread;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TextView view=new TextView(this);view.setText("Private SCO query contract");setContentView(view);
        final AudioManager audio=(AudioManager)getSystemService(AUDIO_SERVICE);
        thread=new HandlerThread("conversation-audio-query");thread.start();
        new Handler(thread.getLooper()).post(new Runnable(){public void run(){
            boolean value;
            try {value=audio.isBluetoothScoOn();}
            catch(UnsupportedOperationException failure){
                if(!failure.getMessage().contains("isBluetoothScoOn"))throw failure;
                System.err.println("AUDIO_SCO_FIXTURE=BASELINE_REJECTED|method=isBluetoothScoOn");return;
            }
            for(int i=0;i<32;i++)if(audio.isBluetoothScoOn()!=value)throw new AssertionError("Route changed during bounded query");
            try {
                JSONObject receipt=new JSONObject();receipt.put("sco",value);receipt.put("queries",33);
                receipt.put("handler_thread",Looper.myLooper()!=Looper.getMainLooper());
                receipt.put("rate",Integer.parseInt(audio.getProperty(AudioManager.PROPERTY_OUTPUT_SAMPLE_RATE)));
                receipt.put("pid",android.os.Process.myPid());
                try(FileOutputStream output=openFileOutput("audio.json",MODE_PRIVATE)){output.write(receipt.toString().getBytes("UTF-8"));}
            }catch(Exception failure){throw new RuntimeException(failure);}
            System.err.println("AUDIO_SCO_FIXTURE=PASS|queries=33|sco="+value+"|handler_thread=true");
        }});
    }
    @Override public void onDestroy(){if(thread!=null)thread.quitSafely();super.onDestroy();}
}
