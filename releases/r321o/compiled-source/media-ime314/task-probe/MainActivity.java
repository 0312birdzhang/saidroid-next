package org.example.saildroid.cleartop;
import android.app.*;import android.content.*;import android.os.*;import android.widget.*;
public final class MainActivity extends Activity {
 static int instances,destroyed;int resumes;boolean replacement;
 static void later(Runnable r){new Handler().postDelayed(r,450);}
 static void require(boolean v,String reason){if(!v)throw new AssertionError(reason);}
 @Override public void onCreate(Bundle b){super.onCreate(b);instances++;replacement=getIntent().getBooleanExtra("recreate",false);setContentView(new TextView(this));
  if(replacement){require(instances==2&&destroyed==1&&ChildActivity.destroyed==2,"standard CLEAR_TOP must recreate");System.err.println("SD_CLEAR_TOP=standard_recreated|instances=2|old_destroyed=1");later(()->startActivity(new Intent(this,TaskActivity.class)));}
  else{require(instances==1,"unexpected root instance");later(()->startActivity(new Intent(this,ExistingActivity.class)));}
 }
 @Override protected void onResume(){super.onResume();resumes++;
  if(!replacement&&resumes==2)later(()->startActivity(new Intent(this,ChildActivity.class).putExtra("mode","standard")));
  if(replacement&&resumes==2){require(TaskActivity.instances==1&&TaskActivity.handled==1&&ChildActivity.destroyed==3,"singleTask return differs");Button button=new Button(this);button.setText("Clear-top return touch");button.setOnClickListener(v->{System.err.println("SD_CLEAR_TOP=return_touch_passed|instances=2|destroyed_children=3");button.setText("Return touch passed");});setContentView(button);System.err.println("SD_CLEAR_TOP=flow_passed|single_top=1|single_task=1|standard_recreated=true");}
 }
 @Override protected void onNewIntent(Intent i){super.onNewIntent(i);throw new AssertionError("standard CLEAR_TOP reused instead of recreating");}
 @Override protected void onDestroy(){destroyed++;super.onDestroy();}
}
