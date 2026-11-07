import android.graphics.HardwareRenderer;
import android.graphics.RenderNode;
import android.graphics.RecordingCanvas;
import android.graphics.Paint;
import android.view.Surface;
import android.os.Looper;
import java.lang.reflect.Method;

/** A real Android RenderThread draws display lists into the host GPU queue. */
public final class HwuiWindowProbe {
    public static void main(String[] args) throws Exception {
        SdRuntime.initializeFramework(true);
        SdServices.installAll();Looper.prepareMainLooper();
        SdWindowHost.install(System.getenv("ANDROID_ROOT")+"/lib/libsdwindow.so");
        SdWindowHost.start("SailDroid HWUI GPU probe","saildroid-hwui-probe");
        long pointer=SdWindowHost.nativeHardwareSurface(1,1080,2160);
        if(pointer==0)throw new IllegalStateException("Native Android Surface was not created");
        Surface surface=new Surface();
        Method set=Surface.class.getDeclaredMethod("setNativeObjectLocked",long.class);set.setAccessible(true);set.invoke(surface,pointer);
        HardwareRenderer.setIsolatedProcess(true);
        HardwareRenderer renderer=new HardwareRenderer();
        renderer.setName("SailDroid HWUI native GPU");renderer.setOpaque(true);
        RenderNode node=new RenderNode("SailDroid GPU content");node.setPosition(0,0,1080,2160);
        Paint paint=new Paint();paint.setAntiAlias(true);paint.setTextSize(64);
        renderer.setContentRoot(node);renderer.setSurface(surface);
        for(int frame=0;frame<12;frame++) {
            RecordingCanvas canvas=node.beginRecording(1080,2160);
            if(!canvas.isHardwareAccelerated())throw new AssertionError("RecordingCanvas is not hardware accelerated");
            canvas.drawColor(0xff123044);paint.setColor(0xff21d4b0);
            canvas.drawRoundRect(80+frame*8,400,920,1000,55,55,paint);
            paint.setColor(0xffffffff);canvas.drawText("Android HWUI / RenderThread",72,220,paint);
            canvas.drawText("GPU frame "+frame,150,700,paint);node.endRecording();
            int result=renderer.createRenderRequest().setVsyncTime(System.nanoTime()).setWaitForPresent(true).syncAndDraw();
            System.err.println("SDHWUI_PROBE=frame|index="+frame+"|result="+result+"|recording_canvas_hardware=true");
            if((result&HardwareRenderer.SYNC_LOST_SURFACE_REWARD_IF_FOUND)!=0)throw new AssertionError("HWUI lost GPU Surface");
            Thread.sleep(90);
        }
        renderer.fence();System.err.println("SDHWUI_PROBE=rendered|frames=12|renderer=android-hwui");
        Thread.sleep(1500);renderer.destroy();
        // The Java Surface overrides belong to the software window store in
        // this isolated first gate. Release the test-owned native reference.
        set.invoke(surface,0L);SdWindowHost.nativeHardwareRelease(pointer);SdWindowHost.stop();
        System.exit(0);
    }
}
