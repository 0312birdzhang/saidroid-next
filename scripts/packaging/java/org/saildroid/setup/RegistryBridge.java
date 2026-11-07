package org.saildroid.setup;

import java.io.File;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

/** Runs the installed registry without starting an installer window or a broker. */
public final class RegistryBridge {
    private RegistryBridge() {}
    public static void refresh(String expectedRoot) throws Exception {
        if (expectedRoot == null || !expectedRoot.equals(System.getenv("ANDROID_ROOT")))
            throw new IllegalArgumentException("Selected runtime differs from ANDROID_ROOT");
        Class<?> registry = Class.forName("org.saildroid.manager.SdAppRegistry");
        Method valid = registry.getMethod("validName", String.class);
        Method get = registry.getMethod("get", String.class);
        int count = 0;
        File[] applications = new File("/home/art/apps").listFiles();
        if (applications == null) throw new IllegalStateException("Cannot read installed app store");
        // installed() deliberately tolerates invalid records for the catalog.
        // Setup must instead fail before partially refreshing a damaged store.
        for (File application : applications) {
            if (!(Boolean)valid.invoke(null, application.getName())) continue;
            if (!application.isDirectory() || !application.getCanonicalFile().equals(application.getAbsoluteFile()))
                throw new IllegalStateException("App directory is not a real directory");
            get.invoke(null, application.getName());
            count++;
        }
        try {
            registry.getMethod("refreshLaunchers").invoke(null);
        } catch (InvocationTargetException failure) {
            throw new IllegalStateException("Installed registry refresh failed", failure.getCause());
        }
        System.out.println("SAILDROID_SETUP_REGISTRY=ready|apps=" + count + "|root=" + expectedRoot);
    }
}
