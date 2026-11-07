import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.cert.CertificateException;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.X509TrustManager;

/** No network access: real roots load and an untrusted certificate is rejected. */
public final class TlsTrustProbe {
    public static void main(String[] args) throws Exception {
        TrustManagerFactory factory = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        factory.init((KeyStore) null);
        X509TrustManager manager = null;
        for (TrustManager candidate : factory.getTrustManagers()) {
            if (candidate instanceof X509TrustManager) manager = (X509TrustManager) candidate;
        }
        if (manager == null || manager.getAcceptedIssuers().length == 0) {
            throw new AssertionError("Private host CA roots were not loaded");
        }
        X509Certificate untrusted;
        try (FileInputStream input = new FileInputStream(args[4] + "/untrusted-test-cert.pem")) {
            untrusted = (X509Certificate) CertificateFactory.getInstance("X.509").generateCertificate(input);
        }
        // First show that the negative fixture is a valid self-signed cert.
        untrusted.verify(untrusted.getPublicKey());
        boolean rejected = false;
        try { manager.checkServerTrusted(new X509Certificate[]{untrusted}, "RSA"); }
        catch (CertificateException expected) { rejected = true; }
        if (!rejected) throw new AssertionError("Untrusted self-signed certificate was accepted");
        SSLContext context = SSLContext.getInstance("TLS");
        context.init(null, factory.getTrustManagers(), null);
        if (context.createSSLEngine().getSupportedProtocols().length == 0) {
            throw new AssertionError("TLS engine unavailable");
        }
        System.out.println("TLS_TRUST_TESTS=PASS|roots=" + manager.getAcceptedIssuers().length
                + "|untrusted_rejected=true|network=false");
    }
}
