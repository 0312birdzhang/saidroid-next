import android.os.*;
import android.security.keymaster.*;
import android.security.keystore.*;
import com.android.internal.os.BinderInternal;
import java.nio.file.*;
import java.util.*;

/** Internal VM fixture. Root controller simulates MCE events on a real private
 * D-Bus service. Apps never choose or write the trusted backend state. */
public final class LockStateKeystoreContract {
 static int checks,phaseNumber;
 static void check(boolean yes,String why){if(!yes)throw new AssertionError(why);checks++;}
 static void phase(Path folder,String state)throws Exception {
  String value=(++phaseNumber)+":"+state;Files.write(folder.resolve("request"),value.getBytes("UTF-8"));
  long until=System.nanoTime()+8_000_000_000L;
  while(System.nanoTime()<until){Path ack=folder.resolve("ack");if(Files.exists(ack)&&new String(Files.readAllBytes(ack),"UTF-8").equals(value))return;Thread.sleep(20);}
  throw new AssertionError("Root lock-fixture controller did not acknowledge "+value);
 }
 static KeymasterArguments params(int algorithm,int purpose,byte[]nonce){return algorithm==1||algorithm==3?StandardKeystoreContract.parameters(algorithm):SymmetricKeystoreContract.parameters(algorithm,purpose,nonce);}
 static void denied(IKeystoreService service,String alias,int algorithm,byte[]nonce)throws Exception {
  int purpose=algorithm==32?1:2;StandardKeystoreContract.Operation op=new StandardKeystoreContract.Operation();op.waitFor(service.begin(op.cb,new Binder(),alias,purpose,true,params(algorithm,purpose,nonce),null,-1));check(op.value.resultCode==-72&&op.value.token==null&&op.value.operationHandle==0,"Locked private operation denied for "+alias+": "+op.value.resultCode);
 }
 public static void main(String[]args)throws Exception {
  dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root"),dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
  check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Original native runtime");check(SdBridge.configurePrivateBinder(args[0]),"Actual kernel Binder");check(SdBridge.registerFrameworkNatives()==100,"Matching JNI");SdBridge.startBinderPool();check(android.system.Os.getuid()==10000,"Actual app UID");
  IKeystoreService service=IKeystoreService.Stub.asInterface(BinderInternal.getContextObject());check(service!=null,"Actual remote keystore");Path folder=Paths.get(args[1]);String mode=args[2];byte[]message="Genuine locked-key policy stream".getBytes("UTF-8");
  phase(folder,"unlocked");
  Map<String,Integer> algorithms=new LinkedHashMap<>();for(int algorithm:new int[]{1,3,32,128})algorithms.put("locked-generated-"+algorithm,algorithm);algorithms.put("locked-imported-32",32);algorithms.put("locked-imported-128",128);
  Map<String,byte[]>outputs=new HashMap<>(),nonces=new HashMap<>();
  for(Map.Entry<String,Integer> entry:algorithms.entrySet()){
   String alias=entry.getKey();int algorithm=entry.getValue();
   if(mode.equals("create")){
    KeymasterArguments a=algorithm==1||algorithm==3?StandardKeystoreContract.generation(algorithm):SymmetricKeystoreContract.generation(algorithm);a.addBoolean(KeymasterDefs.KM_TAG_UNLOCKED_DEVICE_REQUIRED);StandardKeystoreContract.Characteristics created=new StandardKeystoreContract.Characteristics();byte[]raw=new byte[32];Arrays.fill(raw,(byte)0x5a);
    created.waitFor(alias.contains("imported")?service.importKey(created.cb,alias,a,3,raw,-1,0):service.generateKey(created.cb,alias,a,null,-1,0));check(created.code==1,"Real native lock-bearing key creation: "+alias+" code="+created.code);
   }
   StandardKeystoreContract.Characteristics got=new StandardKeystoreContract.Characteristics();got.waitFor(service.getKeyCharacteristics(got.cb,alias,null,null,-1));check(got.code==1&&got.value.hwEnforced.size()==0&&got.value.swEnforced.getBoolean(KeymasterDefs.KM_TAG_UNLOCKED_DEVICE_REQUIRED)&&got.value.swEnforced.getUnsignedInt(KeymasterDefs.KM_TAG_USER_ID,-1)==0,"Genuine persisted lock/user authorization: "+alias);
   check(service.exist(alias,10001)==6&&service.exist(alias,0)==6,"No requested UID substitution");
   if(algorithm==1||algorithm==3)outputs.put(alias,StandardKeystoreContract.perform(service,alias,algorithm,2,message,null,1));
   else {SymmetricKeystoreContract.Finished out=SymmetricKeystoreContract.operate(service,alias,algorithm,algorithm==32?0:2,message,null,null,1);outputs.put(alias,out.output);nonces.put(alias,out.nonce);}
  }
  if(mode.equals("create")){StandardKeystoreContract.Characteristics created=new StandardKeystoreContract.Characteristics();created.waitFor(service.generateKey(created.cb,"ordinary-unlocked-policy",SymmetricKeystoreContract.generation(128),null,-1,0));check(created.code==1,"Ordinary untagged key generated");}
  KeymasterArguments forged=StandardKeystoreContract.generation(3);forged.addBoolean(KeymasterDefs.KM_TAG_UNLOCKED_DEVICE_REQUIRED);forged.addUnsignedInt(KeymasterDefs.KM_TAG_USER_ID,1);StandardKeystoreContract.Characteristics invalid=new StandardKeystoreContract.Characteristics();invalid.waitFor(service.generateKey(invalid.cb,"forged-user",forged,null,-1,0));check(invalid.code==-39&&service.exist("forged-user",-1)==7,"Caller cannot supply trusted user identity");
  phase(folder,"locked");check(service.onKeyguardVisibilityChanged(false,0)==-100,"Apps cannot report a trusted unlock through AIDL");
  for(Map.Entry<String,Integer> entry:algorithms.entrySet()){
   String alias=entry.getKey();int algorithm=entry.getValue();denied(service,alias,algorithm,nonces.get(alias));
   if(algorithm==1||algorithm==3)StandardKeystoreContract.perform(service,alias,algorithm,3,message,outputs.get(alias),1);
   else if(algorithm==128)SymmetricKeystoreContract.operate(service,alias,algorithm,3,message,outputs.get(alias),null,1);
   else SymmetricKeystoreContract.operate(service,alias,algorithm,0,message,null,null,1);
  }
  SymmetricKeystoreContract.operate(service,"ordinary-unlocked-policy",128,2,message,null,null,1);
  for(String state:new String[]{"unexpected","missing","impostor","delay"}){phase(folder,state);for(Map.Entry<String,Integer> entry:algorithms.entrySet())denied(service,entry.getKey(),entry.getValue(),nonces.get(entry.getKey()));}
  phase(folder,"unlocked");
  for(Map.Entry<String,Integer> entry:algorithms.entrySet()){
   String alias=entry.getKey();int algorithm=entry.getValue();
   if(algorithm==1||algorithm==3)StandardKeystoreContract.perform(service,alias,algorithm,2,message,null,1);
   else if(algorithm==128)SymmetricKeystoreContract.operate(service,alias,algorithm,2,message,null,null,1);
   else {SymmetricKeystoreContract.Finished plain=SymmetricKeystoreContract.operate(service,alias,algorithm,1,outputs.get(alias),null,nonces.get(alias),1);check(Arrays.equals(plain.output,message),"Native decrypt succeeds after real trusted fixture unlock");}
   if(mode.equals("reopen"))check(service.del(alias,-1)==1,"Owner removes private key");
  }
  if(mode.equals("reopen"))check(service.del("ordinary-unlocked-policy",-1)==1,"Ordinary key cleanup");
  System.out.println("LOCK_STATE_KEYSTORE=PASS|mode="+mode+"|checks="+checks+"|standard_checks="+StandardKeystoreContract.checks+"|symmetric_checks="+SymmetricKeystoreContract.checks+"|actual_root_MCE_fixture=true|actual_original_native_Keymaster=true|phone_touched=false");System.out.flush();System.err.flush();System.exit(0);
 }
}
