package org.example.saildroid.cleartop;
import android.app.*;import android.content.*;import android.os.*;import android.widget.*;
public final class ExistingActivity extends Activity {
 static int instances;
 @Override public void onCreate(Bundle b){super.onCreate(b);instances++;MainActivity.require(instances==1,"singleTop duplicate instance");setContentView(new TextView(this));MainActivity.later(()->startActivity(new Intent(this,ChildActivity.class).putExtra("mode","existing")));}
 @Override protected void onNewIntent(Intent i){super.onNewIntent(i);MainActivity.require(instances==1&&ChildActivity.destroyed==1&&"from-picker".equals(i.getStringExtra("payload")),"singleTop CLEAR_TOP delivery");System.err.println("SD_CLEAR_TOP=single_top_reused|instances=1|payload=from-picker|child_destroyed=1");MainActivity.later(()->finish());}
}
