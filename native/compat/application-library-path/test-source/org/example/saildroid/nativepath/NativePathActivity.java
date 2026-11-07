package org.example.saildroid.nativepath;

import android.app.Activity;
import android.os.Bundle;
import java.io.File;
import java.util.Arrays;

/** Public API proof that app JNI roots do not become system JNI roots. */
public final class NativePathActivity extends Activity {
    private static native int next();
    private static native int loads();
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            String appRoot=new File(getApplicationInfo().nativeLibraryDir).getCanonicalPath();
            String system=System.getProperty("java.library.path");
            for(String path:system.split(File.pathSeparator)) {
                if(new File(path).getCanonicalPath().equals(appRoot)) {
                    throw new AssertionError("Application directory leaked into system library path");
                }
            }
            if(!getClassLoader().toString().contains(appRoot)) {
                throw new AssertionError("Application class loader lost its JNI directory");
            }
            System.loadLibrary("sdapppathfixture");
            if(next()!=81 || loads()!=1)throw new AssertionError("Name load or JNI_OnLoad failed");
            System.load(new File(appRoot,"libsdapppathfixture.so").getPath());
            if(next()!=82 || loads()!=1)throw new AssertionError("Absolute load did not reuse JNI state");
            System.err.println("NATIVE_PATH_FIXTURE=PASS|system-excludes-app=true|app-search=true|jni-loads=1|state=81,82");
        } catch(Throwable failure) {
            System.err.println("NATIVE_PATH_FIXTURE=FAIL|"+failure);
            failure.printStackTrace();
        }
    }
}
