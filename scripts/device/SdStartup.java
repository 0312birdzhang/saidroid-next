/** Monotonic startup phases; never include application data or account values. */
public final class SdStartup {
    private static final long origin=System.nanoTime();
    public static void phase(String name){System.err.println("SDSTARTUP=phase|name="+name+"|elapsed_ms="+(System.nanoTime()-origin)/1000000);}
    private SdStartup(){}
}
