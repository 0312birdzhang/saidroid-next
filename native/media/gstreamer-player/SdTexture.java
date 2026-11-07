/** The candidate's real Android SurfaceTexture/TextureView backend. */
public final class SdTexture {
    private static native void nativeInstall();
    public static void install() {
        System.load(System.getenv("ANDROID_ROOT")+"/lib/libsdtexture-host.so");
        nativeInstall();
        SdMediaPlayer.install();
    }
}
