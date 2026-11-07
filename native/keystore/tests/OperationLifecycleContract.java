import android.os.*;
import android.security.keymaster.*;
import android.security.keystore.*;
import com.android.internal.os.BinderInternal;
import java.util.*;
/** Actual remote service resource pressure and Binder client-death fixture. */
public final class OperationLifecycleContract {
 static void check(boolean yes,String why){if(!yes)throw new AssertionError(why);}
 public static void main(String[] args)throws Exception {
  dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root"),dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
  check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Matching JNI runtime");check(SdBridge.configurePrivateBinder(args[0]),"Real private Binder");check(SdBridge.registerFrameworkNatives()==100,"Original JNI");SdBridge.startBinderPool();check(android.system.Os.getuid()==10000,"Actual owner UID");
  IKeystoreService service=IKeystoreService.Stub.asInterface(BinderInternal.getContextObject());
  if(args[1].equals("verify")){
   StandardKeystoreContract.Operation begun=new StandardKeystoreContract.Operation();begun.waitFor(service.begin(begun.cb,new Binder(),"hmac-generated",2,true,SymmetricKeystoreContract.parameters(128,2,null),null,-1));check(begun.value.resultCode==1,"Native capacity reusable after client death");StandardKeystoreContract.Response abort=new StandardKeystoreContract.Response();abort.waitFor(service.abort(abort.cb,begun.value.token));check(abort.code==1,"Fresh native operation abort");
   System.out.println("OPERATION_LIFECYCLE=verify|actual_native_capacity_reusable=true");
  }else{
   check(service.begin(new StandardKeystoreContract.Operation().cb,new Binder(),"hmac-generated",2,false,SymmetricKeystoreContract.parameters(128,2,null),null,-1)==6,"Ordinary app cannot reserve non-pruneable resources");
   List<IBinder> tokens=new ArrayList<>();Binder application=new Binder();
   for(int i=0;i<64;i++){StandardKeystoreContract.Operation op=new StandardKeystoreContract.Operation();op.waitFor(service.begin(op.cb,application,"hmac-generated",2,true,SymmetricKeystoreContract.parameters(128,2,null),null,-1));check(op.value.resultCode==1,"Pruneable real operation "+i+" result "+op.value.resultCode);tokens.add(op.value.token);}
   StandardKeystoreContract.Operation oldest=new StandardKeystoreContract.Operation();oldest.waitFor(service.update(oldest.cb,tokens.get(0),new KeymasterArguments(),new byte[]{1}));check(oldest.value.resultCode==-28,"Oldest pruned token invalid");
   StandardKeystoreContract.Operation latest=new StandardKeystoreContract.Operation();latest.waitFor(service.update(latest.cb,tokens.get(63),new KeymasterArguments(),new byte[]{1}));check(latest.value.resultCode==1&&latest.value.inputConsumed==1,"Newest operation remains genuine and usable");
   System.out.println("OPERATION_LIFECYCLE=hold-and-exit|operations_started=64|oldest_invalid=true|latest_usable=true|explicit_abort_not_sent=true");
  }
  System.out.flush();System.err.flush();System.exit(0);
 }
}
