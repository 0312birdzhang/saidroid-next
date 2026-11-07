package org.example.saildroid.sendimage314;
import android.app.Activity;
import android.os.Bundle;
import android.graphics.*;
import android.view.View;
public final class MainActivity extends Activity {
 @Override public void onCreate(Bundle state){super.onCreate(state);setContentView(new View(this){
  final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);boolean logged;
  @Override protected void onDraw(Canvas c){int w=getWidth(),h=getHeight();c.drawColor(Color.rgb(19,42,65));paint.setColor(Color.rgb(21,174,144));c.drawRect(0,h*.18f,w,h*.36f,paint);paint.setColor(Color.rgb(246,179,53));c.drawRect(0,h*.66f,w,h*.84f,paint);paint.setColor(Color.WHITE);paint.setTextAlign(Paint.Align.CENTER);paint.setTextSize(w*.085f);c.drawText("SailDroid",w*.5f,h*.47f,paint);paint.setTextSize(w*.045f);c.drawText("IMAGE SEND TEST 314",w*.5f,h*.54f,paint);c.drawText("Generated test image",w*.5f,h*.60f,paint);if(!logged){logged=true;System.err.println("SDSEND_IMAGE_PROBE=drawn|width="+w+"|height="+h+"|content=generated-test-pattern");}}
 });}
}
