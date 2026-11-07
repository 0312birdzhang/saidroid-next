package org.example.saildroid.cover;
import android.app.Activity;
import android.app.Dialog;
import android.os.Bundle;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import android.view.MotionEvent;
import android.widget.Button;
public final class CoverActivity extends Activity {
    private int generation;
    private Probe view;
    @Override public void onCreate(Bundle state){super.onCreate(state);view=new Probe();setContentView(view);}
    private final class Probe extends View {
        private final Paint paint=new Paint();
        Probe(){super(CoverActivity.this);}
        @Override protected void onDraw(Canvas canvas){
            int[] colours=generation%2==0?new int[]{0xffff0000,0xff00ff00,0xff0000ff,0xffffffff}:new int[]{0xff0000ff,0xffff0000,0xff00ff00,0xffffffff};
            for(int i=0;i<4;i++){paint.setColor(colours[i]);canvas.drawRect(0,i*getHeight()/4f,getWidth(),(i+1)*getHeight()/4f,paint);}
            paint.setColor(0xff000000);paint.setTextSize(72);canvas.drawText("COVER "+generation,80,getHeight()-140,paint);
            System.err.println("COVER_PROBE=draw|generation="+generation+"|hardware="+canvas.isHardwareAccelerated()+"|width="+getWidth()+"|height="+getHeight());
        }
        @Override public boolean onTouchEvent(MotionEvent event){
            if(event.getAction()==MotionEvent.ACTION_UP){
                if(event.getX()<getWidth()/2f){generation++;invalidate();System.err.println("COVER_PROBE=tap|generation="+generation);}
                else{
                    final Dialog dialog=new Dialog(CoverActivity.this);Button button=new Button(CoverActivity.this);button.setText("COVER DIALOG");button.setTextSize(32);button.setBackgroundColor(0xff00ffff);button.setOnClickListener(new View.OnClickListener(){public void onClick(View v){dialog.dismiss();System.err.println("COVER_PROBE=dialog-closed");}});dialog.setContentView(button);dialog.getWindow().setLayout(800,600);dialog.show();dialog.getWindow().setLayout(800,600);System.err.println("COVER_PROBE=dialog-open");
                }
            }
            return true;
        }
    }
}
