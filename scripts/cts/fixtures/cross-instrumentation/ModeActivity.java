package org.example.saildroid.instrumenttarget;
import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
public final class ModeActivity extends Activity {
    @Override public void onCreate(Bundle state){super.onCreate(state);TextView content=new TextView(this);content.setText("Private window touch-mode contract");setContentView(content);}
}
