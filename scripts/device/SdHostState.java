/** Bounded read-only native MCE requests. */
public final class SdHostState {
    private SdHostState(){}
    public static String string(String method){return org.saildroid.host.HostApi.mceString(method);}
    public static boolean bool(String method){return org.saildroid.host.HostApi.mceBoolean(method);}
}
