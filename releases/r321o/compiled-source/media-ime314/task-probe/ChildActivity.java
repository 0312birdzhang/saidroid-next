package org.example.saildroid.cleartop;
import android.app.*;import android.content.*;import android.os.*;import android.widget.*;
public final class ChildActivity extends Activity {
 static int destroyed;
 @Override public void onCreate(Bundle b){super.onCreate(b);setContentView(new TextView(this));String mode=getIntent().getStringExtra("mode");MainActivity.later(()->{Intent next;
 if("existing".equals(mode))next=new Intent(this,ExistingActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP).putExtra("payload","from-picker");
 else if("standard".equals(mode))next=new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP).putExtra("recreate",true);
 else next=new Intent(this,TaskActivity.class).putExtra("payload","from-child");startActivity(next);});}
 @Override protected void onDestroy(){destroyed++;System.err.println("SD_CLEAR_TOP=child_destroyed|count="+destroyed);super.onDestroy();}
}
