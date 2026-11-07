import android.app.ActivityThread;
import android.app.Application;
import android.content.pm.ApplicationInfo;
import android.content.res.CompatibilityInfo;
import android.os.*;
import android.security.keystore.AndroidKeyStoreProvider;
import com.android.internal.os.BinderInternal;
import java.lang.reflect.*;
import java.security.*;
import java.io.File;
import java.nio.file.Files;
import java.util.ArrayList;

/** VM-only real parsed APK application binding plus original provider signing.
 * Does not execute an APK Activity/Service, install a global daemon, or claim CTS.
 */
public final class ProviderKeystoreContract {
    static int checks;
    static void check(boolean yes,String reason){if(!yes)throw new AssertionError(reason);checks++;}
    static void set(Object object,String name,Object value)throws Exception{
        Field f=object.getClass().getDeclaredField(name);f.setAccessible(true);f.set(object,value);
    }
    public static void main(String[] args)throws Exception {
        System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root");
        String dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Matching native runtime");
        check(SdBridge.configurePrivateBinder(args[0]),"Actual private Binder");check(SdBridge.registerFrameworkNatives()==100,"Actual JNI");SdBridge.startBinderPool();
        SdCryptoProvider.install();SdTls.install();
        check(SdBridge.installClassLoaderNamespaces(),"Actual classloader namespaces");SdClassLoaderNamespaces.installNativePathListener();check(SdBridge.installGraphicsEnvironment(),"Actual graphics config");
        SdServices.installAll();Looper.prepareMainLooper();
        IBinder remote=BinderInternal.getContextObject();check(remote!=null&&remote.queryLocalInterface("android.security.keystore.IKeystoreService")==null,"Remote key service");
        // Explicit VM bootstrap registration using the existing process-local
        // service-discovery shim. Calls still travel to the real remote service.
        SdServiceManagerStub.put("android.security.keystore",remote);
        ApplicationInfo app=SdApkPackage.applicationInfo();int uid=Integer.parseInt(args[1]);
        check(app.uid==uid&&android.os.Process.myUid()==uid&&android.system.Os.getuid()==uid,"Actual parsed package UID");
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(app.targetSdkVersion);
        Constructor<ActivityThread> ctor=ActivityThread.class.getDeclaredConstructor();ctor.setAccessible(true);ActivityThread thread=ctor.newInstance();
        Method attach=ActivityThread.class.getDeclaredMethod("attach",boolean.class,long.class);attach.setAccessible(true);attach.invoke(thread,false,0L);
        SdServices.bindApplication(app);android.app.LoadedApk loaded=thread.getPackageInfoNoCheck(app,CompatibilityInfo.DEFAULT_COMPATIBILITY_INFO);
        Class<?> type=Class.forName("android.app.ActivityThread$AppBindData");Constructor<?> dc=type.getDeclaredConstructor();dc.setAccessible(true);Object data=dc.newInstance();
        set(data,"appInfo",app);set(data,"info",loaded);set(data,"processName",app.processName);set(data,"compatInfo",CompatibilityInfo.DEFAULT_COMPATIBILITY_INFO);
        set(data,"config",new android.content.res.Configuration(android.content.res.Resources.getSystem().getConfiguration()));set(data,"providers",new ArrayList<android.content.pm.ProviderInfo>());
        set(thread,"mCoreSettings",new Bundle());Method bind=ActivityThread.class.getDeclaredMethod("handleBindApplication",type);bind.setAccessible(true);bind.invoke(thread,data);
        Application actual=ActivityThread.currentApplication();
        Method getApplication=android.app.LoadedApk.class.getDeclaredMethod("getApplication");getApplication.setAccessible(true);
        check(actual!=null&&actual==getApplication.invoke(loaded)&&actual.getPackageName().equals(SdApkPackage.NAME),"Actual LoadedApk Application bound");
        check(actual.getApplicationInfo().uid==uid,"Application context actual UID");
        AndroidKeyStoreProvider.install();android.security.KeyStore keyStore=android.security.KeyStore.getInstance();
        for(String alias:new String[]{"rsa","ec"}){
            KeyPair pair=AndroidKeyStoreProvider.loadAndroidKeyStoreKeyPairFromKeystore(keyStore,alias,-1);
            check(pair.getPrivate().getClass().getName().startsWith("android.security.keystore.AndroidKeyStore"),"Original AndroidKeyStore private key class");
            check(pair.getPrivate().getEncoded()==null,"Private material not exportable through JCA");
            String algorithm=alias.equals("rsa")?"SHA256withRSA":"SHA256withECDSA";byte[] message=("Original provider actual UID "+uid+" "+alias).getBytes("UTF-8");
            Signature signer=Signature.getInstance(algorithm);signer.initSign(pair.getPrivate());signer.update(message);byte[] signature=signer.sign();
            check(signer.getProvider().getName().equals("AndroidKeyStoreBCWorkaround"),"Original AndroidKeyStore signature provider selected");
            Signature verify=Signature.getInstance(algorithm);verify.initVerify(pair.getPublic());verify.update(message);check(verify.verify(signature),"Original provider signature verified");
            byte[] wrong=message.clone();wrong[0]^=1;verify.initVerify(pair.getPublic());verify.update(wrong);check(!verify.verify(signature),"Changed message rejected");
            File out=new File(args[2]);Files.write(new File(out,alias+"-provider-public.der").toPath(),pair.getPublic().getEncoded());Files.write(new File(out,alias+"-provider-message").toPath(),message);Files.write(new File(out,alias+"-provider-signature").toPath(),signature);
            System.out.println("ORIGINAL_KEYSTORE_PROVIDER=ready|uid="+uid+"|algorithm="+algorithm+"|provider="+signer.getProvider().getName()+"|private_encoded_null=true");
        }
        for(String algorithm:new String[]{"RSA","EC"}){
            String alias="jca-generated-"+algorithm.toLowerCase(java.util.Locale.ROOT);
            KeyPairGenerator generator=KeyPairGenerator.getInstance(algorithm,"AndroidKeyStore");
            android.security.keystore.KeyGenParameterSpec.Builder spec=new android.security.keystore.KeyGenParameterSpec.Builder(alias,android.security.keystore.KeyProperties.PURPOSE_SIGN|android.security.keystore.KeyProperties.PURPOSE_VERIFY).setDigests("SHA-256");
            if(algorithm.equals("RSA"))spec.setSignaturePaddings(android.security.keystore.KeyProperties.SIGNATURE_PADDING_RSA_PKCS1);
            else spec.setAlgorithmParameterSpec(new java.security.spec.ECGenParameterSpec("secp256r1"));
            generator.initialize(spec.build());KeyPair pair=generator.generateKeyPair();
            check(pair.getPrivate().getEncoded()==null,"Original JCA-generated private material unavailable");
            java.security.KeyStore store=java.security.KeyStore.getInstance("AndroidKeyStore");store.load(null,null);
            check(store.containsAlias(alias),"Original KeyStore alias exists");
            PrivateKey privateKey=(PrivateKey)store.getKey(alias,null);java.security.cert.Certificate certificate=store.getCertificate(alias);
            check(privateKey!=null&&privateKey.getEncoded()==null&&certificate!=null,"Original SPI loads private object and certificate");
            check(java.util.Arrays.equals(certificate.getPublicKey().getEncoded(),pair.getPublic().getEncoded()),"Actual generated certificate matches native public key");
            certificate.verify(pair.getPublic());check(true,"Real self-signed certificate verified");
            check(store.getCertificateChain(alias).length==1,"Original SPI certificate chain");
            check(java.util.Collections.list(store.aliases()).contains(alias),"Original SPI enumerates alias");
            String signatureAlgorithm=algorithm.equals("RSA")?"SHA256withRSA":"SHA256withECDSA";byte[] message=("Original JCA key generation UID "+uid+" "+algorithm).getBytes("UTF-8");
            Signature sign=Signature.getInstance(signatureAlgorithm);sign.initSign(privateKey);sign.update(message);byte[] signature=sign.sign();
            Signature verify=Signature.getInstance(signatureAlgorithm);verify.initVerify(certificate);verify.update(message);check(verify.verify(signature),"Original JCA generated key signs and verifies");
            File out=new File(args[2]);String label=algorithm.toLowerCase(java.util.Locale.ROOT);Files.write(new File(out,label+"-generated-public.der").toPath(),pair.getPublic().getEncoded());Files.write(new File(out,label+"-generated-message").toPath(),message);Files.write(new File(out,label+"-generated-signature").toPath(),signature);Files.write(new File(out,label+"-generated-certificate.der").toPath(),certificate.getEncoded());
            store.deleteEntry(alias);check(!store.containsAlias(alias)&&store.getCertificate(alias)==null,"Original SPI deletes generated key and certificate");
            System.out.println("ORIGINAL_JCA_KEYPAIR=ready|uid="+uid+"|algorithm="+algorithm+"|real_certificate=true|private_encoded_null=true|deleted=true");
        }
        SymmetricKeystoreContract.provider(uid,new File(args[2]));
        System.out.println("ORIGINAL_KEYSTORE_PROVIDER_CONTRACT=PASS|uid="+uid+"|checks="+checks+"|application="+actual.getPackageName()+"|real_app_bind=true|APK_component_executed=false");
        System.out.flush();System.err.flush();System.exit(0);
    }
}
