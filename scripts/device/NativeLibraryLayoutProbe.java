/** VM-only rejection check: invalid directories must fail before native loading. */
public final class NativeLibraryLayoutProbe {
    public static void main(String[] args) {
        System.load(args[0]);
        if (SdBridge.loadBionicLibrary(args[1] + "/libandroid_runtime.so", args[1])) {
            throw new AssertionError("Host ABI libraries were accepted on the Android loader path");
        }
        System.out.println("NATIVE_LIBRARY_LAYOUT_TESTS=PASS|mixed_directory_rejected=true");
    }
}
