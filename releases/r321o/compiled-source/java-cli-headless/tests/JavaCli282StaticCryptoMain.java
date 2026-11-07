import java.security.MessageDigest;
public final class JavaCli282StaticCryptoMain {
    private static final byte[] HASH;
    static {
        try { HASH=MessageDigest.getInstance("SHA-256").digest(new byte[0]); }
        catch(Exception failure) { throw new ExceptionInInitializerError(failure); }
    }
    public static void main(String[] args) {
        if(HASH.length!=32)throw new AssertionError("Real crypto initialized before user class initializer");
        System.out.println("JAVA_CLI282_STATIC_CRYPTO=PASS|initialized_before_main=true");
    }
}
