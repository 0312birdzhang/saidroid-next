import java.security.Provider;
import java.security.Security;

/** Select the matching Android TLS/crypto implementation already in the component.
 * Application NetworkSecurityConfig installs its trust-manager provider later,
 * during the normal ActivityThread binding. Do not initialize a default TLS
 * context early or substitute a trust manager here.
 */
public final class SdTls {
    private static boolean installed;
    public static synchronized void install() {
        if(installed)return;
        Provider provider=new com.android.org.conscrypt.OpenSSLProvider();
        if(!"AndroidOpenSSL".equals(provider.getName()))
            throw new IllegalStateException("Unexpected platform TLS provider");
        Security.removeProvider(provider.getName());
        if(Security.insertProviderAt(provider,1)!=1)
            throw new IllegalStateException("Cannot install platform TLS provider");
        // Android10 splits TLS/crypto and key/trust factories between two
        // providers. Keep the matching platform factories before the legacy
        // fallback providers; do not construct a default context or trust store.
        Provider jsse = new com.android.org.conscrypt.JSSEProvider();
        if (!"HarmonyJSSE".equals(jsse.getName()))
            throw new IllegalStateException("Unexpected platform key/trust provider");
        Security.removeProvider(jsse.getName());
        if (Security.insertProviderAt(jsse, 2) != 2)
            throw new IllegalStateException("Cannot install platform key/trust provider");
        System.err.println("SDTLS=platform_jsse|provider=" + jsse.getName()
                + "|backend=matching-api29|legacy_providers=retained");
        // Standalone libcore's resource explicitly names WolfSSL factories.
        // Restore the matching platform factory names as well as provider order;
        // SSLSocketFactory observes Security's version and refreshes its cache.
        Security.setProperty("ssl.SocketFactory.provider","com.android.org.conscrypt.OpenSSLSocketFactoryImpl");
        Security.setProperty("ssl.ServerSocketFactory.provider","com.android.org.conscrypt.OpenSSLServerSocketFactoryImpl");
        installed=true;
        System.err.println("SDTLS=platform_provider|provider="+provider.getName()+"|native=matching-api29-javacrypto|trust=application-network-security-config");
    }
}
