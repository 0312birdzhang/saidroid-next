import java.io.File;

/** Capability-specific graphics setup for the real software Surface backend. */
public final class SdSoftwareGraphics {
    private static File requestedShaderCache;
    public static synchronized void configureShaderCache(String filename){
        if(!android.view.ThreadedRenderer.sRendererDisabled)throw new UnsupportedOperationException("A hardware shader producer is not installed");
        File path=new File(filename);File parent=path.getParentFile();
        if(parent!=null&&!parent.isDirectory()&&!parent.mkdirs())throw new IllegalStateException("Cannot create application graphics cache directory");
        requestedShaderCache=path;
        // A software renderer produces no GPU shader binaries. Retain the
        // requested cache location; do not create pretend shader cache data.
    }
}
