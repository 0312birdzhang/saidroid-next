package org.example.saildroid.activitycaller;
import android.app.Activity;import android.os.Bundle;import android.os.Handler;import android.content.Intent;import android.content.ComponentName;import android.widget.TextView;
public class CallerActivity extends Activity {
 int stage;boolean localResult,remoteResult,scheduled;
 static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
 void verifyRoot(){require(getCallingPackage()==null&&getCallingActivity()==null,"Launcher Activity has no result caller");}
 @Override public void onCreate(Bundle state){super.onCreate(state);try{verifyRoot();TextView v=new TextView(this);v.setText("Activity caller identity regression");setContentView(v);}catch(Throwable t){System.err.println("ACTIVITY_CALLER_FIXTURE=FAIL|"+t);t.printStackTrace();stage=99;}}
 @Override public void onResume(){super.onResume();if(scheduled||stage>=99)return;scheduled=true;new Handler().postDelayed(new Runnable(){public void run(){scheduled=false;try{verifyRoot();switch(stage++){
 case 0:startActivityForResult(new Intent(CallerActivity.this,Child.class).putExtra("expectCaller",true),31);break;
 case 1:require(localResult,"Local result arrived before resume");startActivityForResult(new Intent(CallerActivity.this,RemoteCallerActivity.class).putExtra("expectCaller",true),32);break;
 case 2:require(remoteResult,"Remote result arrived before resume");startActivity(new Intent(CallerActivity.this,Child.class));break;
 case 3:startActivity(new Intent(CallerActivity.this,RemoteCallerActivity.class));break;
 case 4:stage=99;System.err.println("ACTIVITY_CALLER_FIXTURE=PASS|root-null=true|local-result=true|remote-result=true|normal-launch-null=true");break;
 default:throw new AssertionError("Unexpected stage");
 }}catch(Throwable t){stage=99;System.err.println("ACTIVITY_CALLER_FIXTURE=FAIL|"+t);t.printStackTrace();}}},400);}
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);require(result==RESULT_OK,"Child identity check failed");if(request==31)localResult=true;else if(request==32)remoteResult=true;else throw new AssertionError("Wrong result identity");System.err.println("ACTIVITY_CALLER_RESULT=PASS|request="+request);}
 public static class Child extends Activity {
  @Override public void onCreate(Bundle state){super.onCreate(state);try{
   boolean expected=getIntent().getBooleanExtra("expectCaller",false);ComponentName caller=expected?new ComponentName(this,CallerActivity.class):null;
   require(java.util.Objects.equals(caller,getCallingActivity()),"Actual component "+getCallingActivity()+" expected "+caller);
   require(java.util.Objects.equals(expected?getPackageName():null,getCallingPackage()),"Calling package differs");
   System.err.println("ACTIVITY_CALLER_CHILD=PASS|remote="+(getClass().getName().endsWith("RemoteCallerActivity"))+"|hasResultCaller="+expected);setResult(RESULT_OK);
  }catch(Throwable t){System.err.println("ACTIVITY_CALLER_FIXTURE=FAIL|"+t);t.printStackTrace();setResult(RESULT_CANCELED);}new Handler().postDelayed(new Runnable(){public void run(){finish();}},150);}
 }
 public static class RemoteChild extends Child {}
}
