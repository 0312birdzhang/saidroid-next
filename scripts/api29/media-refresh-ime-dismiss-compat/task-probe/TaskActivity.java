package org.example.saildroid.cleartop;
import android.app.*;import android.content.*;import android.os.*;import android.widget.*;
public final class TaskActivity extends Activity {
 static int instances,handled;
 @Override public void onCreate(Bundle b){super.onCreate(b);instances++;MainActivity.require(instances==1,"singleTask duplicate instance");setContentView(new TextView(this));MainActivity.later(()->startActivity(new Intent(this,ChildActivity.class).putExtra("mode","task")));}
 @Override protected void onNewIntent(Intent i){super.onNewIntent(i);MainActivity.require(instances==1&&ChildActivity.destroyed==3&&"from-child".equals(i.getStringExtra("payload")),"singleTask delivery");handled++;System.err.println("SD_CLEAR_TOP=single_task_reused|instances=1|payload=from-child|child_destroyed=3");MainActivity.later(()->finish());}
}
