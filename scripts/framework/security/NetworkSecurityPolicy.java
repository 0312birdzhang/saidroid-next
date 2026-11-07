package android.security;

/** API 23 facade backed by the actual newer libcore per-process policy. */
public final class NetworkSecurityPolicy extends libcore.net.NetworkSecurityPolicy {
    private static final NetworkSecurityPolicy INSTANCE = new NetworkSecurityPolicy();
    private volatile boolean cleartextPermitted = true;
    static { libcore.net.NetworkSecurityPolicy.setInstance(INSTANCE); }
    private NetworkSecurityPolicy() {}
    public static NetworkSecurityPolicy getInstance() { return INSTANCE; }
    @Override public boolean isCleartextTrafficPermitted() { return cleartextPermitted; }
    @Override public boolean isCleartextTrafficPermitted(String hostname) { return cleartextPermitted; }
    public void setCleartextTrafficPermitted(boolean permitted) { cleartextPermitted = permitted; }
    @Override public boolean isCertificateTransparencyVerificationRequired(String hostname) {
        // API 23 provides no Certificate Transparency policy configuration.
        return false;
    }
}
