package org.example.saildroid.audioconnection;
import android.app.Activity;
import android.os.Bundle;
import android.media.AudioSystem;
import android.widget.TextView;

public final class MainActivity extends Activity {
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    TextView view=new TextView(this);
    try {
      int speaker=AudioSystem.getDeviceConnectionState(2,"");
      int headset=AudioSystem.getDeviceConnectionState(4,"");
      int headphone=AudioSystem.getDeviceConnectionState(8,"");
      int foreign=AudioSystem.getDeviceConnectionState(2,"not-a-host-device");
      int invalid=AudioSystem.getDeviceConnectionState(0,"");
      if(speaker!=1||headset!=0||headphone!=0||foreign!=0||invalid!=0)
        throw new AssertionError("Speaker/no-accessory fixture precondition or query mismatch: "+speaker+","+headset+","+headphone+","+foreign+","+invalid);
      System.err.println("AUDIO_CONNECTION=PASS|speaker=1|wired_headset=0|wired_headphone=0|foreign_address=0|invalid=0");
      view.setText("Physical speaker connected; wired ports absent");
    } catch(Throwable failure) {
      System.err.println("AUDIO_CONNECTION=FAIL|type="+failure.getClass().getName());
      failure.printStackTrace();view.setText("Query failed: "+failure);
    }
    setContentView(view);
  }
}
