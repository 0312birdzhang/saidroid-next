import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyPairGenerator;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.security.Signature;
import java.util.HashSet;
import java.util.Set;
import javax.crypto.Cipher;
import javax.net.ssl.SSLContext;

/** Native ownership and real provider selection for the ordinary CLI's crypto APIs. */
public final class JavaCli282CryptoNativeMain {
    public static void main(String[] args) throws Exception {
        JavaCli282CryptoMain.main(args);
        String provider;
        switch(args[0]) {
            case "digest": provider=MessageDigest.getInstance("SHA-256").getProvider().getName(); break;
            case "random": provider=new SecureRandom().getProvider().getName(); break;
            case "aes": provider=Cipher.getInstance("AES/GCM/NoPadding").getProvider().getName(); break;
            case "rsa":
                provider=KeyPairGenerator.getInstance("RSA").getProvider().getName();
                if(!provider.equals(Signature.getInstance("SHA256withRSA").getProvider().getName()))
                    throw new AssertionError("RSA generator/signature provider selection");
                break;
            case "tls": provider=SSLContext.getInstance("TLS").getProvider().getName(); break;
            default: throw new IllegalArgumentException(args[0]);
        }
        if(!provider.equals("AndroidOpenSSL"))throw new AssertionError("Actual matching platform provider: "+provider);
        String root=System.getenv("ANDROID_ROOT");
        String maps=new String(Files.readAllBytes(Paths.get("/proc/self/maps")),"UTF-8");
        Set<String> arts=new HashSet<>(),images=new HashSet<>(),cryptos=new HashSet<>();
        for(String line:maps.split("\n")) {
            String[] words=line.trim().split(" +");String path=words[words.length-1];
            if(path.endsWith("/libart.so"))arts.add(path);
            if(path.endsWith(".art"))images.add(path);
            if(path.endsWith("/libjavacrypto.so"))cryptos.add(path);
        }
        if(!arts.equals(java.util.Collections.singleton(root+"/lib/libart.so"))||images.size()!=9
                ||!cryptos.equals(java.util.Collections.singleton(root+"/android-libs/libjavacrypto.so")))
            throw new AssertionError("Actual component-owned ART/crypto/nine images");
        for(String image:images)if(!image.startsWith(root+"/system/framework/arm64/"))throw new AssertionError("Image owner");
        System.out.println("JAVA_CLI282_CRYPTO_NATIVE=PASS|operation="+args[0]+"|provider="+provider+"|images=9|crypto=component-private");
    }
}
