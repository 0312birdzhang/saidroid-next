import android.os.Binder;
import android.os.ServiceSpecificException;
import android.security.keymaster.*;
import android.security.keystore.*;
import java.io.*;
import java.nio.file.Files;
import java.security.*;
import java.util.*;
import javax.crypto.*;
import javax.crypto.spec.*;

/** VM-only genuine native symmetric/import and original JCA provider contract.
 * Keys are newly generated test material, never an existing credential store.
 */
public final class SymmetricKeystoreContract {
    static int checks;
    static void check(boolean yes,String why){if(!yes)throw new AssertionError(why);checks++;}
    static KeymasterArguments generation(int algorithm){
        KeymasterArguments a=new KeymasterArguments();a.addEnum(KeymasterDefs.KM_TAG_ALGORITHM,algorithm);
        a.addUnsignedInt(KeymasterDefs.KM_TAG_KEY_SIZE,256);a.addBoolean(KeymasterDefs.KM_TAG_NO_AUTH_REQUIRED);
        if(algorithm==32){a.addEnums(KeymasterDefs.KM_TAG_PURPOSE,0,1);a.addEnum(KeymasterDefs.KM_TAG_BLOCK_MODE,32);a.addEnum(KeymasterDefs.KM_TAG_PADDING,1);a.addUnsignedInt(KeymasterDefs.KM_TAG_MIN_MAC_LENGTH,128);}
        else {a.addEnums(KeymasterDefs.KM_TAG_PURPOSE,2,3);a.addEnum(KeymasterDefs.KM_TAG_DIGEST,4);a.addUnsignedInt(KeymasterDefs.KM_TAG_MIN_MAC_LENGTH,256);}
        return a;
    }
    static KeymasterArguments parameters(int algorithm,int purpose,byte[] nonce){
        KeymasterArguments a=new KeymasterArguments();
        if(algorithm==32){a.addEnum(KeymasterDefs.KM_TAG_BLOCK_MODE,32);a.addEnum(KeymasterDefs.KM_TAG_PADDING,1);a.addUnsignedInt(KeymasterDefs.KM_TAG_MAC_LENGTH,128);if(nonce!=null)a.addBytes(KeymasterDefs.KM_TAG_NONCE,nonce);}
        else {a.addEnum(KeymasterDefs.KM_TAG_DIGEST,4);if(purpose==2)a.addUnsignedInt(KeymasterDefs.KM_TAG_MAC_LENGTH,256);}return a;
    }
    static final class Finished {byte[] output,nonce;}
    static Finished operate(IKeystoreService s,String alias,int algorithm,int purpose,byte[] input,byte[] signature,byte[] nonce,int expected)throws Exception {
        StandardKeystoreContract.Operation begin=new StandardKeystoreContract.Operation();begin.waitFor(s.begin(begin.cb,new Binder(),alias,purpose,true,parameters(algorithm,purpose,nonce),null,-1));
        check(begin.value.resultCode==1&&begin.value.token!=null,"Genuine symmetric operation began: "+begin.value.resultCode);
        StandardKeystoreContract.Operation update=new StandardKeystoreContract.Operation();update.waitFor(s.update(update.cb,begin.value.token,new KeymasterArguments(),input));
        check(update.value.resultCode==1&&update.value.inputConsumed==input.length,"Genuine symmetric input consumed");
        StandardKeystoreContract.Operation finish=new StandardKeystoreContract.Operation();finish.waitFor(s.finish(finish.cb,begin.value.token,new KeymasterArguments(),signature,null));
        check(finish.value.resultCode==expected,"Genuine symmetric finish: "+finish.value.resultCode+" expected "+expected);
        StandardKeystoreContract.Operation stale=new StandardKeystoreContract.Operation();stale.waitFor(s.update(stale.cb,begin.value.token,new KeymasterArguments(),input));check(stale.value.resultCode==-28,"Symmetric operation token retired");
        Finished out=new Finished();ByteArrayOutputStream collected=new ByteArrayOutputStream();if(update.value.output!=null)collected.write(update.value.output);if(finish.value.output!=null)collected.write(finish.value.output);out.output=collected.toByteArray();out.nonce=begin.value.outParams.getBytes(KeymasterDefs.KM_TAG_NONCE,null);return out;
    }
    static void raw(IKeystoreService service,int uid,String mode,File out)throws Exception {
        int before=checks;byte[] message=("Real native Keymaster stream actual UID "+uid).getBytes("UTF-8");
        for(int algorithm:new int[]{32,128})for(boolean imported:new boolean[]{false,true}){
            String alias=(algorithm==32?"aes":"hmac")+(imported?"-imported":"-generated");
            // Distinct, public test-only fixture bytes; not account credentials.
            byte[] source=new byte[32];for(int i=0;i<source.length;i++)source[i]=(byte)(uid+i*17+algorithm);
            if(mode.equals("create")){
                StandardKeystoreContract.Characteristics created=new StandardKeystoreContract.Characteristics();
                created.waitFor(imported?service.importKey(created.cb,alias,generation(algorithm),3,source,-1,0):service.generateKey(created.cb,alias,generation(algorithm),null,-1,0));
                check(created.code==1&&created.value!=null,"Native symmetric generation/import: "+alias+" result "+created.code);
                check(created.value.hwEnforced.size()==0&&created.value.swEnforced.getEnum(KeymasterDefs.KM_TAG_ALGORITHM,-1)==algorithm,"Genuine symmetric characteristics");
                check(created.value.swEnforced.getEnum(KeymasterDefs.KM_TAG_ORIGIN,-1)==(imported?2:0),"Genuine native generated/imported origin");
                StandardKeystoreContract.Characteristics duplicate=new StandardKeystoreContract.Characteristics();duplicate.waitFor(service.importKey(duplicate.cb,alias,generation(algorithm),3,source,-1,0));check(duplicate.code==16,"Import cannot overwrite key");
            }
            StandardKeystoreContract.Export exported=new StandardKeystoreContract.Export();exported.waitFor(service.exportKey(exported.cb,alias,3,null,null,-1));check(exported.value.resultCode==-17,"Secret RAW export denied");
            boolean denied=false;try{service.get(alias,-1);}catch(ServiceSpecificException e){denied=e.errorCode==6;}check(denied,"Secret blob get denied");check(service.insert(alias,source,-1,0)==6,"Value cannot overwrite symmetric key");
            check(service.exist(alias,uid==10000?10001:10000)==6,"Symmetric explicit other UID denied");
            if(algorithm==32){
                Finished encrypted=operate(service,alias,algorithm,0,message,null,null,1);check(encrypted.nonce!=null&&encrypted.nonce.length==12&&encrypted.output.length==message.length+16,"Native GCM nonce/ciphertext/tag");
                Finished decrypted=operate(service,alias,algorithm,1,encrypted.output,null,encrypted.nonce,1);check(Arrays.equals(decrypted.output,message),"Native GCM round trip");
                byte[] altered=encrypted.output.clone();altered[altered.length-1]^=1;operate(service,alias,algorithm,1,altered,null,encrypted.nonce,-30);
                if(imported){Cipher verifier=Cipher.getInstance("AES/GCM/NoPadding","AndroidOpenSSL");verifier.init(Cipher.DECRYPT_MODE,new SecretKeySpec(source,"AES"),new GCMParameterSpec(128,encrypted.nonce));check(Arrays.equals(verifier.doFinal(encrypted.output),message),"Independent non-keystore AES validates imported material");}
                Files.write(new File(out,alias+"-ciphertext").toPath(),encrypted.output);
            }else{
                Finished signed=operate(service,alias,algorithm,2,message,null,null,1);check(signed.output.length==32,"Actual HMAC256 output");operate(service,alias,algorithm,3,message,signed.output,null,1);byte[] altered=signed.output.clone();altered[0]^=1;operate(service,alias,algorithm,3,message,altered,null,-30);
                if(imported){Mac verifier=Mac.getInstance("HmacSHA256","AndroidOpenSSL");verifier.init(new SecretKeySpec(source,"HmacSHA256"));check(Arrays.equals(signed.output,verifier.doFinal(message)),"Independent non-keystore HMAC validates imported material");}
                Files.write(new File(out,alias+"-mac").toPath(),signed.output);
            }
            Arrays.fill(source,(byte)0);
            if(mode.equals("reopen"))check(service.del(alias,-1)==1&&service.exist(alias,-1)==7,"Owner symmetric deletion after complete backend restart");
        }
        if(mode.equals("create")){
            for(int algorithm:new int[]{32,128}){
                StandardKeystoreContract.Characteristics bad=new StandardKeystoreContract.Characteristics();KeymasterArguments auth=generation(algorithm);auth.addBoolean(KeymasterDefs.KM_TAG_UNLOCKED_DEVICE_REQUIRED);bad.waitFor(service.importKey(bad.cb,"locked-import-"+algorithm,auth,3,new byte[32],-1,0));check(bad.code==-39&&service.exist("locked-import-"+algorithm,-1)==7,"Import rejects unsupported lock authorization");
                StandardKeystoreContract.Characteristics format=new StandardKeystoreContract.Characteristics();format.waitFor(service.importKey(format.cb,"bad-format-"+algorithm,generation(algorithm),1,new byte[32],-1,0));check(format.code==-17&&service.exist("bad-format-"+algorithm,-1)==7,"Import rejects wrong format without persistent key");
            }
            StandardKeystoreContract.Characteristics malformed=new StandardKeystoreContract.Characteristics();malformed.waitFor(service.importKey(malformed.cb,"malformed",generation(32),3,new byte[7],-1,0));check(malformed.code!=1&&service.exist("malformed",-1)==7,"Original HAL rejects malformed AES material");
        }
        if(mode.equals("create")){
            for(String policy:new String[]{"purpose","future","expired-origin","expired-consumption"}){
                KeymasterArguments a=generation(128);
                if(policy.equals("purpose")){
                    a=new KeymasterArguments();a.addEnum(KeymasterDefs.KM_TAG_ALGORITHM,128);a.addUnsignedInt(KeymasterDefs.KM_TAG_KEY_SIZE,256);a.addEnum(KeymasterDefs.KM_TAG_PURPOSE,3);a.addEnum(KeymasterDefs.KM_TAG_DIGEST,4);a.addUnsignedInt(KeymasterDefs.KM_TAG_MIN_MAC_LENGTH,256);a.addBoolean(KeymasterDefs.KM_TAG_NO_AUTH_REQUIRED);
                }else a.addDate(policy.equals("future")?KeymasterDefs.KM_TAG_ACTIVE_DATETIME:policy.equals("expired-origin")?KeymasterDefs.KM_TAG_ORIGINATION_EXPIRE_DATETIME:KeymasterDefs.KM_TAG_USAGE_EXPIRE_DATETIME,new java.util.Date(System.currentTimeMillis()+(policy.equals("future")?3600000:-3600000)));
                String alias="policy-"+policy;StandardKeystoreContract.Characteristics created=new StandardKeystoreContract.Characteristics();created.waitFor(service.generateKey(created.cb,alias,a,null,-1,0));check(created.code==1,"Generate genuine policy-bearing key");
                int purpose=policy.equals("expired-consumption")?3:2,expected=policy.equals("purpose")?-3:policy.equals("future")?-24:-25;
                StandardKeystoreContract.Operation denied=new StandardKeystoreContract.Operation();denied.waitFor(service.begin(denied.cb,new Binder(),alias,purpose,true,parameters(128,purpose,null),null,-1));check(denied.value.resultCode==expected&&denied.value.token==null,"Genuine purpose/date rejection "+policy+": "+denied.value.resultCode);
                if(policy.equals("expired-consumption")){StandardKeystoreContract.Operation allowed=new StandardKeystoreContract.Operation();allowed.waitFor(service.begin(allowed.cb,new Binder(),alias,2,true,parameters(128,2,null),null,-1));check(allowed.value.resultCode==1,"Consumption expiry does not prevent origination");StandardKeystoreContract.Response ended=new StandardKeystoreContract.Response();ended.waitFor(service.abort(ended.cb,allowed.value.token));check(ended.code==1,"Allowed policy operation abort");}
                check(service.del(alias,-1)==1,"Policy fixture deleted");
            }
            StandardKeystoreContract.Operation nonce=new StandardKeystoreContract.Operation();nonce.waitFor(service.begin(nonce.cb,new Binder(),"aes-generated",0,true,parameters(32,0,new byte[12]),null,-1));check(nonce.value.resultCode==-55&&nonce.value.token==null,"Caller nonce rejected without genuine key authorization");
        }
        System.out.println("SYMMETRIC_RAW=ready|uid="+uid+"|mode="+mode+"|checks="+(checks-before)+"|genuine_native_AES_GCM_HMAC=true|no_secret_export=true");
    }
    static void provider(int uid,File output)throws Exception {
        int before=checks;java.security.KeyStore store=java.security.KeyStore.getInstance("AndroidKeyStore");store.load(null,null);
        for(String algorithm:new String[]{"AES","HmacSHA256"})for(boolean imported:new boolean[]{false,true}){
            String alias="jca-symmetric-"+algorithm+"-"+imported;byte[] raw=new byte[32];new SecureRandom().nextBytes(raw);
            android.security.keystore.KeyGenParameterSpec.Builder generation=new android.security.keystore.KeyGenParameterSpec.Builder(alias,algorithm.equals("AES")?3:12).setKeySize(256);
            android.security.keystore.KeyProtection.Builder protection=new android.security.keystore.KeyProtection.Builder(algorithm.equals("AES")?3:12);
            if(algorithm.equals("AES")){generation.setBlockModes("GCM").setEncryptionPaddings("NoPadding");protection.setBlockModes("GCM").setEncryptionPaddings("NoPadding");}
            else {generation.setDigests("SHA-256");protection.setDigests("SHA-256");}
            SecretKey key;
            if(imported){store.setEntry(alias,new java.security.KeyStore.SecretKeyEntry(new SecretKeySpec(raw,algorithm)),protection.build());key=(SecretKey)store.getKey(alias,null);}
            else {KeyGenerator generator=KeyGenerator.getInstance(algorithm,"AndroidKeyStore");generator.init(generation.build());key=generator.generateKey();}
            check(key!=null&&key.getEncoded()==null&&key.getClass().getName().startsWith("android.security.keystore.AndroidKeyStore"),"Original nonexportable JCA secret object");
            check(store.containsAlias(alias)&&store.isKeyEntry(alias)&&store.getCertificate(alias)==null,"Original SPI secret key entry");
            byte[] message=("Original AndroidKeyStore symmetric UID "+uid).getBytes("UTF-8");
            if(algorithm.equals("AES")){
                Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key);byte[] encrypted=cipher.doFinal(message);byte[] nonce=cipher.getIV();check(cipher.getProvider().getName().equals("AndroidKeyStoreBCWorkaround"),"Original AndroidKeyStore cipher selected");
                Cipher decrypt=Cipher.getInstance("AES/GCM/NoPadding");decrypt.init(Cipher.DECRYPT_MODE,key,new GCMParameterSpec(128,nonce));check(Arrays.equals(decrypt.doFinal(encrypted),message),"Original JCA native GCM round trip");
                byte[] tampered=encrypted.clone();tampered[tampered.length-1]^=1;boolean rejected=false;try{decrypt.init(Cipher.DECRYPT_MODE,key,new GCMParameterSpec(128,nonce));decrypt.doFinal(tampered);}catch(AEADBadTagException expected){rejected=true;}check(rejected,"Original JCA maps authentication failure to AEADBadTagException");
                if(imported){Cipher independent=Cipher.getInstance("AES/GCM/NoPadding","AndroidOpenSSL");independent.init(Cipher.DECRYPT_MODE,new SecretKeySpec(raw,"AES"),new GCMParameterSpec(128,nonce));check(Arrays.equals(independent.doFinal(encrypted),message),"Independent AES validates original SPI imported key");}
            }else{
                Mac mac=Mac.getInstance("HmacSHA256");mac.init(key);byte[] value=mac.doFinal(message);check(mac.getProvider().getName().equals("AndroidKeyStoreBCWorkaround")&&value.length==32,"Original JCA native HMAC");
                if(imported){Mac independent=Mac.getInstance("HmacSHA256","AndroidOpenSSL");independent.init(new SecretKeySpec(raw,"HmacSHA256"));check(Arrays.equals(independent.doFinal(message),value),"Independent HMAC validates original SPI imported key");}
            }
            store.deleteEntry(alias);check(!store.containsAlias(alias),"Original SPI deletes secret key");Arrays.fill(raw,(byte)0);
        }
        // Original service PKCS8 import against independent software-generated pairs.
        IKeystoreService service=IKeystoreService.Stub.asInterface(com.android.internal.os.BinderInternal.getContextObject());
        for(int algorithm:new int[]{1,3}){
            String name=algorithm==1?"RSA":"EC",alias="pkcs8-import-"+name;KeyPairGenerator gen=KeyPairGenerator.getInstance(name,"AndroidOpenSSL");if(algorithm==1)gen.initialize(2048);else gen.initialize(new java.security.spec.ECGenParameterSpec("secp256r1"));KeyPair pair=gen.generateKeyPair();byte[] pkcs8=pair.getPrivate().getEncoded();
            StandardKeystoreContract.Characteristics imported=new StandardKeystoreContract.Characteristics();imported.waitFor(service.importKey(imported.cb,alias,StandardKeystoreContract.generation(algorithm),1,pkcs8,-1,0));check(imported.code==1,"Real native PKCS8 import "+name+" result "+imported.code);Arrays.fill(pkcs8,(byte)0);
            StandardKeystoreContract.Export exported=new StandardKeystoreContract.Export();exported.waitFor(service.exportKey(exported.cb,alias,0,null,null,-1));check(exported.value.resultCode==1&&Arrays.equals(exported.value.exportData,pair.getPublic().getEncoded()),"PKCS8 native public key matches original source");
            byte[] message=("Native PKCS8 actual UID "+uid+" "+name).getBytes("UTF-8");byte[] signature=StandardKeystoreContract.perform(service,alias,algorithm,2,message,null,1);Signature verifier=Signature.getInstance(algorithm==1?"SHA256withRSA":"SHA256withECDSA","AndroidOpenSSL");verifier.initVerify(pair.getPublic());verifier.update(message);check(verifier.verify(signature),"Independent native provider validates imported PKCS8 signature");check(service.del(alias,-1)==1,"Imported asymmetric key deleted");
        }
        System.out.println("SYMMETRIC_ORIGINAL_JCA=ready|uid="+uid+"|checks="+(checks-before)+"|AES_GCM_HMAC_generation_import=true|PKCS8_RSA_EC=true|private_encoded_null=true");
    }
}
