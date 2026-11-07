import android.os.*;
import android.security.keymaster.*;
import android.security.keystore.*;
import com.android.internal.os.BinderInternal;
import java.nio.file.*;
import java.util.*;

/** Internal VM AIDL diagnostic. Explicitly independent of original CTS secure
 * lockscreen eligibility; no original test method or assertion is executed. */
public final class AttestationStandardContract {
    static void check(boolean ok,String why){StandardKeystoreContract.check(ok,why);}
    static final class Chain extends StandardKeystoreContract.Await {
        int code;KeymasterCertificateChain chain;
        final IKeystoreCertificateChainCallback cb=new IKeystoreCertificateChainCallback.Stub(){
            public void onFinished(KeystoreResponse response,KeymasterCertificateChain certs){
                StandardKeystoreContract.callback();code=response.getErrorCode();chain=certs;done.countDown();
            }
        };
    }
    static Chain attest(IKeystoreService s,String alias,KeymasterArguments args,int expected)throws Exception{
        Chain c=new Chain();c.waitFor(s.attestKey(c.cb,alias,args));check(c.code==expected,"Actual expected native attestation result "+expected+", got "+c.code);return c;
    }
    public static void main(String[]args)throws Exception{
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root");
        String dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Actual native runtime");check(SdBridge.configurePrivateBinder(args[0]),"Actual private Binder");check(SdBridge.registerFrameworkNatives()==100,"Actual JNI");SdBridge.startBinderPool();
        int own=Integer.parseInt(args[1]);check(android.os.Process.myUid()==own&&android.system.Os.getuid()==own,"Actual client kernel UID");
        IKeystoreService service=IKeystoreService.Stub.asInterface(BinderInternal.getContextObject());check(service!=null,"Actual remote key service");
        if(args[2].equals("unknown")){
            KeymasterArguments a=new KeymasterArguments();a.addBytes(KeymasterDefs.KM_TAG_ATTESTATION_CHALLENGE,new byte[17]);attest(service,"attested-1",a,6);
            check(service.exist("attested-1",10000)==6,"Other UID cannot select original APK key namespace");
        }else{
            for(int alg:new int[]{1,3}){
                String alias="attested-"+alg;StandardKeystoreContract.Characteristics gen=new StandardKeystoreContract.Characteristics();gen.waitFor(service.generateKey(gen.cb,alias,StandardKeystoreContract.generation(alg),null,-1,0));check(gen.code==1&&gen.value.hwEnforced.size()==0,"Genuine software key");
                try{
                    StandardKeystoreContract.Export exported=new StandardKeystoreContract.Export();exported.waitFor(service.exportKey(exported.cb,alias,0,null,null,-1));check(exported.value.resultCode==1,"Actual native public key");Files.write(Paths.get(args[3],"alg"+alg+"-public.der"),exported.value.exportData);
                    for(int length:new int[]{0,17,128}){
                        byte[] challenge=new byte[length];for(int i=0;i<length;i++)challenge[i]=(byte)i;
                        KeymasterArguments a=new KeymasterArguments();a.addBytes(KeymasterDefs.KM_TAG_ATTESTATION_CHALLENGE,challenge);Chain c=attest(service,alias,a,1);List<byte[]> certificates=c.chain.getCertificates();check(certificates.size()==3,"Original native three-certificate chain");
                        for(int i=0;i<certificates.size();i++)Files.write(Paths.get(args[3],"alg"+alg+"-ch"+length+"-cert"+i+".der"),certificates.get(i));
                    }
                    KeymasterArguments forged=new KeymasterArguments();forged.addBytes(KeymasterDefs.KM_TAG_ATTESTATION_CHALLENGE,new byte[17]);forged.addBytes(0x900002c5 /* official API29 native KM_BYTES|709 */,"forged caller identity".getBytes("UTF-8"));Chain denied=attest(service,alias,forged,6);check(denied.chain.getCertificates().isEmpty(),"No certificate for caller-forged app identity");
                    KeymasterArguments tooLarge=new KeymasterArguments();tooLarge.addBytes(KeymasterDefs.KM_TAG_ATTESTATION_CHALLENGE,new byte[129]);attest(service,alias,tooLarge,-21);
                    attest(service,alias,new KeymasterArguments(),-63);
                }finally{check(service.del(alias,-1)==1&&service.exist(alias,-1)==7,"Ephemeral native key removed");}
            }
        }
        System.out.println("STANDARD_ATTESTATION=PASS|uid="+own+"|mode="+args[2]+"|checks="+StandardKeystoreContract.checks+"|real_callbacks="+StandardKeystoreContract.callbacks+"|original_CTS=false|hardware=false");System.out.flush();System.err.flush();System.exit(0);
    }
}
