package org.example.saildroid.windowhaptics;

import android.app.Activity;
import android.os.Bundle;
import android.view.HapticFeedbackConstants;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Public View APIs exercise the real API29 IWindowSession proxy. */
public final class MainActivity extends Activity {
    private TextView status;
    private Button target;
    private boolean checked;
    private int longPresses;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);
        status=new TextView(this);status.setTextSize(22);status.setText("Haptic feedback: waiting for real window focus");
        content.addView(status,new LinearLayout.LayoutParams(-1,180));
        target=new Button(this);target.setText("Long press twice");
        target.setOnLongClickListener(new View.OnLongClickListener(){public boolean onLongClick(View view){
            longPresses++;status.setText("Long presses handled: "+longPresses);
            System.err.println("SDHAPTIC_PROBE=long_press_handled|count="+longPresses);
            return true;
        }});
        content.addView(target,new LinearLayout.LayoutParams(-1,240));
        setContentView(content);
    }
    @Override public void onWindowFocusChanged(boolean focus) {
        super.onWindowFocusChanged(focus);
        if(!focus||checked)return;checked=true;
        int calls=0;
        for(int effect:new int[]{HapticFeedbackConstants.LONG_PRESS,HapticFeedbackConstants.KEYBOARD_TAP,HapticFeedbackConstants.VIRTUAL_KEY}) {
            for(int flags:new int[]{0,HapticFeedbackConstants.FLAG_IGNORE_VIEW_SETTING|HapticFeedbackConstants.FLAG_IGNORE_GLOBAL_SETTING}) {
                boolean supported=target.performHapticFeedback(effect,flags);
                if(supported)throw new AssertionError("Host has no vibrator backend");
                calls++;
            }
        }
        status.setText("Unsupported vibration returned false: "+calls+" calls");
        System.err.println("SDHAPTIC_PROBE=api_passed|calls="+calls+"|supported=false");
    }
}
