package org.example.saildroid.audio;
import android.app.Activity;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.os.Bundle;
import android.widget.TextView;
import org.json.JSONObject;
import java.io.FileOutputStream;

public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TextView view = new TextView(this); view.setText("Private audio property contract"); setContentView(view);
        AudioManager audio = (AudioManager)getSystemService(AUDIO_SERVICE);
        final String rate;
        try { rate = audio.getProperty(AudioManager.PROPERTY_OUTPUT_SAMPLE_RATE); }
        catch (UnsatisfiedLinkError expected) {
            if (!expected.getMessage().contains("getPrimaryOutputSamplingRate")) throw expected;
            System.err.println("AUDIO_FIXTURE=BASELINE_REJECTED|missing=getPrimaryOutputSamplingRate"); return;
        }
        int hz = Integer.parseInt(rate);
        if (hz <= 0) throw new AssertionError("Sampling rate must be real and positive");
        String frames = audio.getProperty(AudioManager.PROPERTY_OUTPUT_FRAMES_PER_BUFFER);
        if (frames != null) throw new AssertionError("Backend does not expose Android HAL frame count");
        boolean listed = false;
        for (AudioDeviceInfo device : audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS))
            for (int supported : device.getSampleRates()) if (supported == hz) listed = true;
        if (!listed) throw new AssertionError("Default sink sampling rate absent from host audio ports");
        try {
            JSONObject row = new JSONObject(); row.put("rate",hz); row.put("frames",JSONObject.NULL);
            row.put("rate_in_host_ports",listed);row.put("volume",audio.getStreamVolume(AudioManager.STREAM_MUSIC));
            row.put("pid",android.os.Process.myPid());
            try (FileOutputStream output = openFileOutput("audio.json",MODE_PRIVATE)) {
                output.write(row.toString().getBytes("UTF-8"));
            }
        } catch (Exception failure) { throw new RuntimeException(failure); }
        System.err.println("AUDIO_FIXTURE=PASS|rate="+hz+"|frames=null|rate_in_host_ports=true");
    }
}
