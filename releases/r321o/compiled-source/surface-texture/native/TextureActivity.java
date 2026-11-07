package org.example.saildroid.texture;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.SurfaceTexture;
import android.opengl.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.util.concurrent.*;

/** Real BufferQueue -> SurfaceTexture -> HWUI TextureView pixel contract. */
public final class TextureActivity extends Activity implements TextureView.SurfaceTextureListener {
    private final Handler main=new Handler(Looper.getMainLooper());
    private TextureView texture;
    private SurfaceTexture consumer;
    private final Semaphore mayRender=new Semaphore(1);
    private final int[] expected={Color.RED,Color.GREEN,Color.BLUE};
    private volatile int produced,consumed;
    private volatile boolean finished;
    private final CountDownLatch renderDone=new CountDownLatch(1);
    private void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);
        TextView title=new TextView(this);title.setText("SurfaceTexture real GPU queue contract");layout.addView(title);
        texture=new TextureView(this);texture.setSurfaceTextureListener(this);
        layout.addView(texture,new LinearLayout.LayoutParams(600,600));setContentView(layout);
        main.postDelayed(new Runnable(){public void run(){if(!finished)throw new AssertionError("Texture roundtrip deadline");}},35000);
    }
    public void onSurfaceTextureAvailable(final SurfaceTexture target,int width,int height){
        consumer=target;require(texture.isHardwareAccelerated(),"TextureView must use HWUI");
        new Thread(new Runnable(){public void run(){
            EGLDisplay display=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
            int[] versions=new int[2];require(EGL14.eglInitialize(display,versions,0,versions,1),"EGL initialize");
            EGLConfig[] configs=new EGLConfig[1];int[] count=new int[1];
            int[] attrs={EGL14.EGL_RENDERABLE_TYPE,EGL14.EGL_OPENGL_ES2_BIT,EGL14.EGL_SURFACE_TYPE,EGL14.EGL_WINDOW_BIT,EGL14.EGL_RED_SIZE,8,EGL14.EGL_GREEN_SIZE,8,EGL14.EGL_BLUE_SIZE,8,EGL14.EGL_ALPHA_SIZE,8,EGL14.EGL_NONE};
            require(EGL14.eglChooseConfig(display,attrs,0,configs,0,1,count,0)&&count[0]>0,"EGL window config");
            EGLContext context=EGL14.eglCreateContext(display,configs[0],EGL14.EGL_NO_CONTEXT,new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION,2,EGL14.EGL_NONE},0);
            require(context!=null&&context!=EGL14.EGL_NO_CONTEXT,"EGL context");
            Surface producer=new Surface(target);
            EGLSurface surface=EGL14.eglCreateWindowSurface(display,configs[0],producer,new int[]{EGL14.EGL_NONE},0);
            require(surface!=null&&surface!=EGL14.EGL_NO_SURFACE,"Real producer EGL window error="+EGL14.eglGetError());
            require(EGL14.eglMakeCurrent(display,surface,surface,context),"Producer makeCurrent");
            try{
                for(int index=0;index<expected.length;index++){
                    require(mayRender.tryAcquire(8,TimeUnit.SECONDS),"Consumer acknowledgment");
                    int color=expected[index];GLES20.glViewport(0,0,600,600);
                    GLES20.glClearColor(Color.red(color)/255f,Color.green(color)/255f,Color.blue(color)/255f,1f);
                    GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
                    require(GLES20.glGetError()==GLES20.GL_NO_ERROR,"Producer GLES clear");
                    produced=index+1;require(EGL14.eglSwapBuffers(display,surface),"Real queue swap");
                    System.err.println("TEXTURE_FIXTURE=produced|frame="+produced+"|renderer="+GLES20.glGetString(GLES20.GL_RENDERER));
                }
                require(mayRender.tryAcquire(8,TimeUnit.SECONDS),"Final consumer acknowledgment");
            }catch(InterruptedException failure){throw new RuntimeException(failure);}
            finally{
                EGL14.eglMakeCurrent(display,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT);
                require(EGL14.eglDestroySurface(display,surface),"Producer EGL surface destruction");
                require(EGL14.eglDestroyContext(display,context),"Producer context destruction");
                producer.release();require(!producer.isValid(),"Producer Surface reference released");EGL14.eglReleaseThread();renderDone.countDown();
                // Display belongs to this application's shared HWUI/native path.
                // Do not terminate it underneath the active RenderThread.
            }
        }},"Texture-real-producer").start();
    }
    public void onSurfaceTextureUpdated(SurfaceTexture value){
        final int index=produced;
        if(index<=consumed||index<=0||index>expected.length)return;
        Bitmap bitmap=texture.getBitmap(64,64);require(bitmap!=null,"Real TextureView pixel snapshot");
        int pixel=bitmap.getPixel(32,32);bitmap.recycle();int color=expected[index-1];
        require(Math.abs(Color.red(pixel)-Color.red(color))<=3&&Math.abs(Color.green(pixel)-Color.green(color))<=3&&Math.abs(Color.blue(pixel)-Color.blue(color))<=3,"Consumed pixels differ frame="+index+" pixel="+Integer.toHexString(pixel));
        consumed=index;System.err.println("TEXTURE_FIXTURE=consumed|frame="+index+"|pixel="+Integer.toHexString(pixel)+"|source=TextureView.getBitmap");mayRender.release();
        if(index==expected.length)main.postDelayed(new Runnable(){public void run(){
            require(renderDone.getCount()==0,"Producer resources released");require(texture.isAvailable(),"Consumer still owns texture");
            ((android.view.ViewGroup)texture.getParent()).removeView(texture);
            main.postDelayed(new Runnable(){public void run(){require(consumer.isReleased(),"Consumer SurfaceTexture released");finished=true;System.err.println("TEXTURE_FIXTURE=PASS|frames=3|real_pixels=true|producer_released=true|consumer_removed=true");}},300);
        }},500);
    }
    public void onSurfaceTextureSizeChanged(SurfaceTexture value,int width,int height){}
    public boolean onSurfaceTextureDestroyed(SurfaceTexture value){System.err.println("TEXTURE_FIXTURE=consumer_destroyed");return true;}
}
