public class SdBridge {
    public static native boolean configurePrivateBinder(String path);
    public static native void startBinderPool();
    public static native boolean becomeBinderContextManager(android.os.IBinder manager);
    public static native boolean loadBionicLibrary(String path, String dirs);
    public static native long lookupSymbol(String sym);
    public static native int registerFrameworkNatives();
    public static native String selfTestVmRuntime();
    public static native String checkGraphicsInit();
    public static native String nativeAssetProbe(String libdir);
    public static native boolean addBionicLibraryPath(String dirs);
    public static native boolean installClassLoaderNamespaces();
    public static native boolean installGraphicsEnvironment();
    public static native void installExitDiagnostics();
}
