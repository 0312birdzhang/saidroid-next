package org.example.saildroid.hwuiprobe;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.os.Handler;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class HwuiActivity extends Activity {
    int count;TextView state;
    final class GpuView extends View {
        final Paint paint=new Paint(3);boolean reported;
        GpuView(Context context){super(context);}
        @Override protected void onDraw(Canvas canvas) {
            if(!reported){
                System.err.println("SDHWUI_APP=draw|view_hardware="+isHardwareAccelerated()+"|canvas_hardware="+canvas.isHardwareAccelerated());
                boolean expected=(getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_HARDWARE_ACCELERATED)!=0;
                if(isHardwareAccelerated()!=expected||canvas.isHardwareAccelerated()!=expected)throw new AssertionError("View renderer differs from APK contract");
                reported=true;
            }
            canvas.drawColor(0xff123044);paint.setColor(0xff21d4b0);
            canvas.drawRoundRect(50,70,getWidth()-50,getHeight()-70,40,40,paint);
            paint.setColor(Color.WHITE);paint.setTextSize(54);canvas.drawText("Native Android View",90,180,paint);
            canvas.drawText("GPU count "+count,90,280,paint);
        }
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setBackgroundColor(0xff123044);
        state=new TextView(this);state.setTextColor(Color.WHITE);state.setTextSize(24);state.setText("HWUI touch count 0");box.addView(state,new LinearLayout.LayoutParams(-1,180));
        final GpuView gpu=new GpuView(this);box.addView(gpu,new LinearLayout.LayoutParams(-1,700));
        Button button=new Button(this);button.setText("Increment GPU scene");box.addView(button,new LinearLayout.LayoutParams(-1,260));
        button.setOnClickListener(new View.OnClickListener(){public void onClick(View view){count++;state.setText("HWUI touch count "+count);gpu.invalidate();System.err.println("SDHWUI_APP=click|count="+count+"|view_hardware="+view.isHardwareAccelerated());}});
        Button dialog=new Button(this);dialog.setText("Open Android dialog");box.addView(dialog,new LinearLayout.LayoutParams(-1,260));
        dialog.setOnClickListener(new View.OnClickListener(){public void onClick(View view){new AlertDialog.Builder(HwuiActivity.this).setTitle("GPU dialog").setMessage("A second native EGL window").setPositiveButton("Close",(d,w)->{System.err.println("SDHWUI_APP=dialog_closed");}).show();System.err.println("SDHWUI_APP=dialog_open");}});
        setContentView(box);System.err.println("SDHWUI_APP=created");
    }
}
