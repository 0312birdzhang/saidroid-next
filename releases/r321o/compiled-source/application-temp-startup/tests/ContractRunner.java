/** VM diagnostic driver using the original APK's JUnit and actual callbacks. */
public final class TempStartup237ContractRunner {
    public static void main(String[] args) throws Exception {
        int sdk = Integer.parseInt(args[2]);
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(sdk);
        if (dalvik.system.VMRuntime.getRuntime().getTargetSdkVersion() != sdk)
            throw new AssertionError("Original target SDK was not bound");
        System.load(System.getProperty("saidroid.bridge.library"));
        Class<?> bridge = Class.forName("SdBridge");
        String root = System.getProperty("saidroid.native.root");
        String dirs = root + "/lib64:" + root + "/apex/com.android.runtime.debug/lib64:"
                + root + "/apex/com.android.conscrypt/lib64:" + root + "/apex/com.android.resolv/lib64";
        if (!(Boolean) bridge.getMethod("loadBionicLibrary", String.class, String.class).invoke(
                null, root + "/lib64/libandroid_runtime.so", dirs))
            throw new AssertionError("Actual product native bootstrap failed");
        int registered = (Integer) bridge.getMethod("registerFrameworkNatives").invoke(null);
        if (registered != 104) throw new AssertionError("Actual product JNI registrations: " + registered);
        // These are the same platform initialization calls used by SdRuntime,
        // before any app/test class loads. They initialize the real Security
        // providers and their lifetime boot-resource cache.
        Class.forName("SdCryptoProvider").getMethod("install").invoke(null);
        Class.forName("SdTls").getMethod("install").invoke(null);
        if (!(Boolean) bridge.getMethod("installClassLoaderNamespaces").invoke(null))
            throw new AssertionError("Actual application namespace backend unavailable");
        Class.forName("SdClassLoaderNamespaces").getMethod("installNativePathListener").invoke(null);
        System.out.println("PLATFORM_CORE_BOOTSTRAP|registered=" + registered
                + "|uid=" + android.system.Os.getuid());
        ClassLoader loader = new dalvik.system.PathClassLoader(
                args[0] + java.io.File.pathSeparator + args[3],
                System.getProperty("saidroid.test.apk.native"), Object.class.getClassLoader());
        if (!(Boolean)bridge.getMethod("addBionicLibraryPath",String.class).invoke(null,
                System.getProperty("saidroid.test.apk.native")))
            throw new AssertionError("Actual APK native search path registration failed");
        Thread.currentThread().setContextClassLoader(loader);
        System.setProperty("java.io.tmpdir",System.getenv("TMPDIR"));
        System.setProperty("user.home",System.getenv("HOME"));
        java.util.Set<String> mapped=new java.util.HashSet<>();
        for(String line:java.nio.file.Files.readAllLines(java.nio.file.Paths.get("/proc/self/maps"))) {
            String path=line.substring(line.lastIndexOf(" ")+1);
            if(path.endsWith("/libopenjdk.so"))mapped.add(path);
        }
        if(!mapped.equals(java.util.Collections.singleton("/var/tmp/saidroid-actual-phone-openjdk-20261031/libopenjdk.so")))
            throw new AssertionError("Actual phone native library mapping differs: "+mapped);
        System.out.println("ACTUAL_PHONE_OPENJDK_MAP="+mapped.iterator().next());
        for (String property : new String[]{"saidroid.test.character.helper", "saidroid.test.fdlibm.helper"}) {
            String expected = System.getProperty(property);
            if (expected == null) throw new AssertionError("Native helper identity required");
            java.util.Set<String> owners = new java.util.HashSet<>();
            for (String line : java.nio.file.Files.readAllLines(java.nio.file.Paths.get("/proc/self/maps"))) {
                String path = line.substring(line.lastIndexOf(" ") + 1);
                if (path.endsWith("/" + new java.io.File(expected).getName())) owners.add(path);
            }
            if (!owners.equals(java.util.Collections.singleton(expected)))
                throw new AssertionError("Actual native helper mapping differs: " + owners);
        }
        System.out.println("FINAL_NATIVE_COMPONENT_MAP=verified|original_phone_openjdk=true|character63=true|fdlibm=true|namespace=actual-product");
        java.util.Set<String> images = new java.util.HashSet<>();
        java.util.Set<String> arts = new java.util.HashSet<>();
        for (String line : java.nio.file.Files.readAllLines(java.nio.file.Paths.get("/proc/self/maps"))) {
            String path = line.substring(line.lastIndexOf(" ") + 1);
            if (path.endsWith(".art")) images.add(path);
            if (path.endsWith("/libart.so")) arts.add(path);
        }
        java.util.Set<String> expected = new java.util.HashSet<>(java.util.Arrays.asList(
                System.getProperty("saidroid.test.boot-images").split(";")));
        if (!images.equals(expected) || !arts.equals(java.util.Collections.singleton(
                System.getProperty("saidroid.test.art")))) throw new AssertionError("Actual ART/boot mappings differ: " + arts + " / " + images);
        System.out.println("OJ195_BOOT_IMAGES=verified|count=" + images.size());
        java.util.Set<String> javacore = new java.util.HashSet<>();
        for(String line : java.nio.file.Files.readAllLines(java.nio.file.Paths.get("/proc/self/maps"))) {
            String path=line.substring(line.lastIndexOf(" ")+1);
            if(path.endsWith("/libjavacore.so"))javacore.add(path);
        }
        if(!javacore.equals(java.util.Collections.singleton(System.getProperty("saidroid.test.javacore"))))throw new AssertionError("Actual javacore mapping differs: "+javacore);
        System.out.println("NATIVE196_JAVACORE_MAP=verified|path="+javacore.iterator().next());
        ApplicationTempStartupContract.run(args[1]);
        System.out.flush(); System.err.flush(); System.exit(0);
    }
}
