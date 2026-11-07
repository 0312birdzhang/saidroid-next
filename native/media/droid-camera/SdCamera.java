/** Android Camera1 access backed by the phone's isolated droidmedia helper. */
public final class SdCamera {
    private static boolean installed;
    private static native void nativeInstall();
    private static native int nativeCount();
    public static synchronized void install(){if(installed)return;System.load(System.getenv("ANDROID_ROOT")+"/lib/libsdcamera-host.so");nativeInstall();SdCameraAppOps.install();SdCameraPolicy.install();installed=true;}
    public static boolean available(){return installed&&nativeCount()>0;}
    public static void enforceAccess(){
        try{if(!new SdAppPermissions(SdApkPackage.APK,SdApkPackage.NAME).holds("android.permission.CAMERA"))throw new SecurityException("Camera access requires explicit application permission");}
        catch(SecurityException failure){throw failure;}
        catch(Exception failure){throw new IllegalStateException("Cannot verify camera permission",failure);}
    }
}
