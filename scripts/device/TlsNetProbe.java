import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.security.KeyStore;
import java.security.cert.Certificate;
import java.security.cert.X509Certificate;
import java.util.Arrays;
import java.util.Enumeration;

import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.TrustManager;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.X509TrustManager;

/**
 * Decides why TLS verification fails (-329) inside the deployed SailDroid runtime.
 * Prints the environment the wolfSSL trust manager actually sees, the root count of
 * every candidate trust store, and the result of a real handshake. No fakes: if a
 * store is empty it says so, and a failed handshake prints the exception chain.
 */
public final class TlsNetProbe {
    private static void line(String s) {
        System.out.println("TLSPROBE=" + s);
    }

    private static void probeDir(String label, String path) {
        File dir = new File(path);
        boolean exists = dir.exists();
        String[] files = exists ? dir.list() : null;
        int count = files == null ? -1 : files.length;
        line("path|" + label + "|" + path + "|exists=" + exists + "|entries=" + count);
        if (count > 0) {
            String[] sample = files.clone();
            Arrays.sort(sample);
            line("path_sample|" + label + "|" + sample[0]);
        }
    }

    private static void probeFile(String label, String path) {
        File f = new File(path);
        line("file|" + label + "|" + path + "|exists=" + f.exists() + "|size="
                + (f.exists() ? f.length() : -1) + "|readable=" + f.canRead());
    }

    private static void rootCount(String label, KeyStore store) {
        int n = 0;
        try {
            Enumeration<String> aliases = store.aliases();
            while (aliases.hasMoreElements()) {
                aliases.nextElement();
                n++;
            }
        } catch (Exception e) {
            line("store_count_error|" + label + "|" + e);
            return;
        }
        line("store_count|" + label + "|" + n);
    }

    private static void trustManagerRoots(String label, String algorithm, String provider) {
        try {
            TrustManagerFactory tmf = provider == null
                    ? TrustManagerFactory.getInstance(algorithm)
                    : TrustManagerFactory.getInstance(algorithm, provider);
            tmf.init((KeyStore) null);
            line("tmf|" + label + "|provider=" + tmf.getProvider().getName()
                    + "|algorithm=" + tmf.getAlgorithm());
            int roots = 0;
            for (TrustManager tm : tmf.getTrustManagers()) {
                line("tm|" + label + "|class=" + tm.getClass().getName());
                if (tm instanceof X509TrustManager) {
                    X509Certificate[] issuers = ((X509TrustManager) tm).getAcceptedIssuers();
                    roots = issuers == null ? -1 : issuers.length;
                    line("tm_roots|" + label + "|" + roots);
                }
            }
        } catch (Throwable t) {
            line("tmf_error|" + label + "|" + t.getClass().getName() + "|" + t.getMessage());
        }
    }

    private static void handshake(String label, String host, int port, String protocol) {
        long started = System.nanoTime();
        try {
            SSLContext ctx = SSLContext.getInstance(protocol);
            ctx.init(null, null, null);
            try (SSLSocket socket = (SSLSocket) ctx.getSocketFactory().createSocket()) {
                socket.connect(new InetSocketAddress(host, port), 8000);
                socket.setSoTimeout(8000);
                socket.startHandshake();
                X509Certificate peer = (X509Certificate) socket.getSession().getPeerCertificates()[0];
                long ms = (System.nanoTime() - started) / 1000000L;
                line("handshake|OK|" + label + "|" + protocol + "|" + host + "|" + ms + "ms"
                        + "|cipher=" + socket.getSession().getCipherSuite()
                        + "|subject=" + peer.getSubjectDN().getName()
                        + "|issuer=" + peer.getIssuerDN().getName());
            }
        } catch (Throwable t) {
            long ms = (System.nanoTime() - started) / 1000000L;
            Throwable cause = t;
            StringBuilder chain = new StringBuilder();
            while (cause != null) {
                chain.append(cause.getClass().getName()).append(':')
                        .append(cause.getMessage()).append(" <- ");
                cause = cause.getCause();
            }
            line("handshake|FAIL|" + label + "|" + protocol + "|" + host + "|" + ms + "ms|chain=" + chain);
        }
    }

    /** Loads every PEM under the private CA directory into a fresh JKS, like wolfSSL does. */
    private static void loadPrivateStore(String dir) {
        File f = new File(dir);
        String[] files = f.list();
        if (files == null) {
            line("private_store|MISSING|" + dir);
            return;
        }
        try {
            KeyStore store = KeyStore.getInstance("JKS");
            store.load(null, null);
            java.security.cert.CertificateFactory cf =
                    java.security.cert.CertificateFactory.getInstance("X.509");
            int ok = 0;
            int bad = 0;
            for (String name : files) {
                try (InputStream in = new FileInputStream(new File(f, name))) {
                    Certificate cert = cf.generateCertificate(in);
                    store.setCertificateEntry("alias" + ok, cert);
                    ok++;
                } catch (Throwable t) {
                    bad++;
                    if (bad <= 3) {
                        line("private_store_bad|" + name + "|" + t.getClass().getName() + "|" + t.getMessage());
                    }
                }
            }
            line("private_store|LOADED|" + dir + "|files=" + files.length + "|ok=" + ok + "|bad=" + bad);
        } catch (Throwable t) {
            line("private_store|FAIL|" + dir + "|" + t);
        }
    }

    public static void main(String[] args) {
        line("start|begin");
        line("env|ANDROID_ROOT|" + System.getenv("ANDROID_ROOT"));
        line("env|ANDROID_DATA|" + System.getenv("ANDROID_DATA"));
        line("env|JAVA_HOME|" + System.getenv("JAVA_HOME"));
        line("env|XDG_DATA_DIRS|" + System.getenv("XDG_DATA_DIRS"));
        line("prop|java.home|" + System.getProperty("java.home"));
        line("prop|java.vm.vendor|" + System.getProperty("java.vm.vendor"));
        line("prop|java.version|" + System.getProperty("java.version"));
        line("prop|javax.net.ssl.trustStore|" + System.getProperty("javax.net.ssl.trustStore"));
        line("prop|javax.net.ssl.trustStoreType|" + System.getProperty("javax.net.ssl.trustStoreType"));
        line("prop|wolfjsse.debug|" + System.getProperty("wolfjsse.debug"));

        String androidRoot = System.getenv("ANDROID_ROOT");
        probeFile("host_java_cacerts", "/etc/ssl/certs/java/cacerts");
        if (androidRoot != null) {
            probeDir("android_root_cacerts", androidRoot + "/etc/security/cacerts");
        } else {
            line("path|android_root_cacerts|ANDROID_ROOT null");
        }
        probeDir("private_cacerts", "/home/art/etc/security/cacerts");

        // Does the AndroidCAStore SPI exist at all in this libcore?
        try {
            KeyStore acs = KeyStore.getInstance("AndroidCAStore");
            acs.load(null, null);
            line("android_ca_store|AVAILABLE|provider=" + acs.getProvider().getName());
            rootCount("android_ca_store", acs);
        } catch (Throwable t) {
            line("android_ca_store|UNAVAILABLE|" + t.getClass().getName() + "|" + t.getMessage());
        }

        loadPrivateStore("/home/art/etc/security/cacerts");
        if (androidRoot != null) {
            loadPrivateStore(androidRoot + "/etc/security/cacerts");
        }

        trustManagerRoots("default", "X509", null);
        trustManagerRoots("wolfssl", "X509", "wolfSSL");
        trustManagerRoots("pkix", "PKIX", null);

        handshake("example.com", "example.com", 443, "TLS");
        handshake("ti.qq.com", "ti.qq.com", 443, "TLS");
        handshake("www.qq.com", "www.qq.com", 443, "TLSv1.2");

        line("start|done");
    }
}
