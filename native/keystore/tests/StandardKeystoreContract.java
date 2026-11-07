import org.saildroid.keystore.NativeSoftwareKeymaster;
import org.saildroid.keystore.SoftwareKeystoreService;
import android.os.*;
import android.security.keymaster.*;
import android.security.keystore.*;
import com.android.internal.os.BinderInternal;
import java.io.File;
import java.nio.file.Files;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Actual original IKeystoreService proxy/stub/callbacks, internal VM contract. */
public final class StandardKeystoreContract {
    static int checks=0,callbacks=0;
    static void check(boolean yes,String why){if(!yes)throw new AssertionError(why);checks++;}
    static void callback(){check(Binder.isHandlingTransaction()&&Binder.getCallingUid()==10050,"Real service callback UID");callbacks++;}
    static abstract class Await {
        final CountDownLatch done=new CountDownLatch(1);
        void waitFor(int dispatch)throws Exception {check(dispatch==1,"AIDL dispatch accepted");check(done.await(5,TimeUnit.SECONDS),"Original async callback arrived");}
    }
    static final class Characteristics extends Await {
        int code;KeyCharacteristics value;
        final IKeystoreKeyCharacteristicsCallback cb=new IKeystoreKeyCharacteristicsCallback.Stub(){
            public void onFinished(KeystoreResponse response,KeyCharacteristics c){callback();code=response.getErrorCode();value=c;done.countDown();}
        };
    }
    static final class Export extends Await {
        ExportResult value;
        final IKeystoreExportKeyCallback cb=new IKeystoreExportKeyCallback.Stub(){
            public void onFinished(ExportResult r){callback();value=r;done.countDown();}
        };
    }
    static final class Operation extends Await {
        OperationResult value;
        final IKeystoreOperationResultCallback cb=new IKeystoreOperationResultCallback.Stub(){
            public void onFinished(OperationResult r){callback();value=r;done.countDown();}
        };
    }
    static final class Response extends Await {
        int code;
        final IKeystoreResponseCallback cb=new IKeystoreResponseCallback.Stub(){
            public void onFinished(KeystoreResponse r){callback();code=r.getErrorCode();done.countDown();}
        };
    }
    static KeymasterArguments generation(int algorithm) {
        KeymasterArguments a=new KeymasterArguments();
        a.addEnum(KeymasterDefs.KM_TAG_ALGORITHM,algorithm);
        a.addUnsignedInt(KeymasterDefs.KM_TAG_KEY_SIZE,algorithm==1?2048:256);
        a.addEnums(KeymasterDefs.KM_TAG_PURPOSE,2,3);
        a.addEnum(KeymasterDefs.KM_TAG_DIGEST,4);
        a.addBoolean(KeymasterDefs.KM_TAG_NO_AUTH_REQUIRED);
        if(algorithm==1){a.addUnsignedLong(KeymasterDefs.KM_TAG_RSA_PUBLIC_EXPONENT,BigInteger.valueOf(65537));a.addEnum(KeymasterDefs.KM_TAG_PADDING,5);}
        return a;
    }
    static KeymasterArguments parameters(int algorithm) {
        KeymasterArguments a=new KeymasterArguments();a.addEnum(KeymasterDefs.KM_TAG_DIGEST,4);
        if(algorithm==1)a.addEnum(KeymasterDefs.KM_TAG_PADDING,5);return a;
    }
    static byte[] perform(IKeystoreService service,String alias,int algorithm,int purpose,
            byte[] message,byte[] signature,int expected)throws Exception {
        Operation begin=new Operation();begin.waitFor(service.begin(begin.cb,new Binder(),alias,purpose,true,parameters(algorithm),null,-1));
        check(begin.value.resultCode==1&&begin.value.token!=null&&begin.value.operationHandle!=0,"Actual native operation began");
        Operation update=new Operation();update.waitFor(service.update(update.cb,begin.value.token,new KeymasterArguments(),message));
        check(update.value.resultCode==1&&update.value.inputConsumed==message.length,"Actual native update consumed input");
        Operation finish=new Operation();finish.waitFor(service.finish(finish.cb,begin.value.token,new KeymasterArguments(),signature,null));
        check(finish.value.resultCode==expected,"Actual native finish result "+finish.value.resultCode+" expected "+expected);
        Operation stale=new Operation();stale.waitFor(service.update(stale.cb,begin.value.token,new KeymasterArguments(),message));
        check(stale.value.resultCode==-28,"Finished token invalidated");return finish.value.output;
    }
    public static void main(String[]args)throws Exception {
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);
        System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root");
        String dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Native runtime load");
        check(SdBridge.configurePrivateBinder(args[1]),"Actual Binder configure");check(SdBridge.registerFrameworkNatives()==100,"Matching original JNI");SdBridge.startBinderPool();
        int own=Integer.parseInt(args[2]);check(android.os.Process.myUid()==own&&android.system.Os.getuid()==own,"Actual own UID");
        if(args[0].equals("server")) {
            System.load(args[6]);
            NativeSoftwareKeymaster.initialize(Integer.parseInt(args[7]),new int[]{10000,10001},args[8],args[9],args[10]);
            check(SdBridge.becomeBinderContextManager(new SoftwareKeystoreService()),"Standard AIDL real context manager");
            File ready=new File(args[4]),stop=new File(args[5]);Files.write(ready.toPath(),"ready\n".getBytes("UTF-8"));
            long deadline=System.nanoTime()+75_000_000_000L;
            while(!stop.exists()&&System.nanoTime()<deadline)Thread.sleep(25);
            check(stop.exists(),"Supervisor completion");NativeSoftwareKeymaster.close();
            System.out.println("STANDARD_KEYSTORE_SERVER=ready|native_closed=true|checks="+checks);
        } else {
            IKeystoreService service=IKeystoreService.Stub.asInterface(BinderInternal.getContextObject());
            check(service!=null&&!(service instanceof SoftwareKeystoreService),"Original remote proxy");
            String mode=args[3];int other=own==10000?10001:10000;
            if(mode.equals("unknown")){check(service.exist("rsa",-1)==6,"Unknown kernel UID denied");}
            else {
                check(service.exist("rsa",other)==6&&service.exist("rsa",0)==6,"Cannot request another UID or root");
                check(service.is_hardware_backed("RSA")==0,"Software backend hardware claim false");
                check(service.onUserPasswordChanged(0,"never-stored")==-100,"Auth backend explicitly unsupported");
                if(mode.equals("create")){
                    check(service.exist("rsa",-1)==7,"Own empty namespace");
                    for(int algorithm:new int[]{1,3}) {
                        String alias=algorithm==1?"rsa":"ec";
                        Characteristics generated=new Characteristics();generated.waitFor(service.generateKey(generated.cb,alias,generation(algorithm),null,-1,0));
                        check(generated.code==1&&generated.value!=null,"Genuine native key generated");
                        check(generated.value.hwEnforced.size()==0&&generated.value.swEnforced.getEnum(KeymasterDefs.KM_TAG_ALGORITHM,-1)==algorithm,"Actual software characteristics");
                        Characteristics duplicate=new Characteristics();duplicate.waitFor(service.generateKey(duplicate.cb,alias,generation(algorithm),null,-1,0));check(duplicate.code==16,"Duplicate cannot replace key");
                    }
                    Characteristics bad=new Characteristics();KeymasterArguments auth=generation(1);auth.addUnsignedLong(KeymasterDefs.KM_TAG_USER_SECURE_ID,BigInteger.ONE);
                    bad.waitFor(service.generateKey(bad.cb,"auth-denied",auth,null,-1,0));check(bad.code==-39,"Unsupported authentication tag rejected");
                    check(service.exist("auth-denied",-1)==7,"No auth key silently created");
                    Characteristics flags=new Characteristics();check(service.generateKey(flags.cb,"strongbox",generation(1),null,-1,16)==-100,"StrongBox flags unsupported");
                }
                byte[] value=("non-secret value UID "+own).getBytes("UTF-8");
                if(mode.equals("create")){
                    check(service.insert("cert-value",value,-1,0)==1,"Own typed value insert");
                    check(service.insert("cert-empty",new byte[0],-1,0)==1,"Empty typed value insert");
                    check(service.insert("cert-value",new byte[]{1,2},-1,0)==1&&service.insert("cert-value",value,-1,0)==1,"Atomic same-kind value replacement");
                    check(service.insert("rsa",value,-1,0)==6,"Value cannot replace a native private key");
                    check(service.insert("encrypted",value,-1,1)==-100,"Encrypted-at-rest flag unsupported");
                }
                check(Arrays.equals(service.get("cert-value",-1),value),"Own value data survives service restart");
                check(service.get("cert-empty",-1).length==0,"Empty typed value round trip");
                check(Arrays.asList(service.list("cert-",-1)).containsAll(Arrays.asList("value","empty")),"Original prefix-stripped alias listing");
                boolean privateDenied=false;try{service.get("rsa",-1);}catch(ServiceSpecificException expected){privateDenied=expected.errorCode==6;}check(privateDenied,"Native private blob cannot be read through get");
                boolean crossDenied=false;try{service.get("cert-value",other);}catch(ServiceSpecificException expected){crossDenied=expected.errorCode==6;}check(crossDenied,"Value read cannot request other UID");
                if(mode.equals("reopen")){check(service.del("cert-value",-1)==1&&service.del("cert-empty",-1)==1,"Owner deletes typed values");}
                for(int algorithm:new int[]{1,3}){
                    String alias=algorithm==1?"rsa":"ec";
                    Characteristics existing=new Characteristics();existing.waitFor(service.getKeyCharacteristics(existing.cb,alias,null,null,-1));check(existing.code==1&&existing.value.hwEnforced.size()==0,"Durable actual characteristics");
                    Export exported=new Export();exported.waitFor(service.exportKey(exported.cb,alias,0,null,null,-1));check(exported.value.resultCode==1&&exported.value.exportData.length>64,"Real X509 public export");
                    byte[] message=("VM actual original AIDL UID "+own+" "+mode+" "+alias).getBytes("UTF-8");
                    byte[] signature=perform(service,alias,algorithm,2,message,null,1);check(signature!=null&&signature.length>32,"Genuine native signature bytes");
                    perform(service,alias,algorithm,3,message,signature,1);byte[] bad=message.clone();bad[0]^=1;perform(service,alias,algorithm,3,bad,signature,-30);
                    File output=new File(args[4]);Files.write(new File(output,alias+"-public.der").toPath(),exported.value.exportData);Files.write(new File(output,alias+"-message").toPath(),message);Files.write(new File(output,alias+"-signature").toPath(),signature);
                    if(mode.equals("reopen")){check(service.del(alias,-1)==1&&service.exist(alias,-1)==7,"Own durable key deletion");}
                }
            }
            if(!mode.equals("unknown")){SdCryptoProvider.install();SdTls.install();SymmetricKeystoreContract.raw(service,own,mode,new File(args[4]));}
            System.out.println("STANDARD_KEYSTORE_CLIENT=ready|uid="+own+"|mode="+mode+"|checks="+checks+"|real_callbacks="+callbacks);
        }
        System.out.flush();System.err.flush();System.exit(0);
    }
}
