import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.security.Signature;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.net.ssl.SSLContext;

/** Ordinary CLI application: no platform bootstrap, native load or test-only API. */
public final class JavaCli282CryptoMain {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        check(JavaCli282CryptoMain.class.getClassLoader() == ClassLoader.getSystemClassLoader(), "Actual application loader");
        byte[] text = "independent ordinary CLI crypto".getBytes(StandardCharsets.UTF_8);
        String operation = args[0];
        if (operation.equals("digest")) {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(text);
            check(digest.length == 32, "Actual SHA256 output");
            StringBuilder hex = new StringBuilder();
            for (byte b : digest) hex.append(String.format("%02x", b & 255));
            check(hex.toString().equals("2e8b503fd4de42cc98b477a17009b195becbac6949b76d35140619c19330eb3b"), "Independent known digest");
        } else if (operation.equals("random")) {
            byte[] a = new byte[32], b = new byte[32];
            SecureRandom random = new SecureRandom();
            random.nextBytes(a); random.nextBytes(b);
            check(!Arrays.equals(a, b) && !Arrays.equals(a, new byte[32]), "Fresh real random bytes");
        } else if (operation.equals("aes")) {
            KeyGenerator generator = KeyGenerator.getInstance("AES"); generator.init(128);
            SecretKey key = generator.generateKey();
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key);
            byte[] encrypted = cipher.doFinal(text);
            javax.crypto.spec.GCMParameterSpec iv = new javax.crypto.spec.GCMParameterSpec(128, cipher.getIV());
            cipher.init(Cipher.DECRYPT_MODE, key, iv);
            check(Arrays.equals(text, cipher.doFinal(encrypted)), "Actual AES GCM roundtrip");
        } else if (operation.equals("rsa")) {
            KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA"); generator.initialize(2048);
            KeyPair pair = generator.generateKeyPair();
            Signature signature = Signature.getInstance("SHA256withRSA"); signature.initSign(pair.getPrivate()); signature.update(text);
            byte[] bytes = signature.sign(); signature.initVerify(pair.getPublic()); signature.update(text);
            check(signature.verify(bytes), "Actual RSA sign verify");
        } else if (operation.equals("tls")) {
            SSLContext context = SSLContext.getInstance("TLS"); context.init(null, null, null);
            check(context.getSocketFactory() != null && context.getDefaultSSLParameters().getProtocols().length > 0, "Real TLS context factories");
        } else throw new IllegalArgumentException(operation);
        System.out.println("JAVA_CLI282_CRYPTO=PASS|operation=" + operation + "|loader=application");
    }
}
