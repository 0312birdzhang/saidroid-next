package org.example.saildroid.webviewprobe;
import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.webkit.*;
import android.view.WindowManager;

public final class WebViewProbeActivity extends Activity {
    WebView web;
    int finished;
    boolean retried;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,WindowManager.LayoutParams.FLAG_FULLSCREEN);
        web=new WebView(this);setContentView(web);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.setWebChromeClient(new WebChromeClient(){
            @Override public void onReceivedTitle(WebView v,String title){System.err.println("SDWEBPROBE=title|value="+title);}
        });
        web.setWebViewClient(new WebViewClient(){
            @Override public void onPageFinished(WebView v,String url){
                System.err.println("SDWEBPROBE=finished|count="+(++finished)+"|url="+url);
                v.evaluateJavascript("JSON.stringify({answer:7*6,scroll:scrollY,dpr:devicePixelRatio,innerWidth:innerWidth,innerHeight:innerHeight,text:document.getElementById('result').textContent})",new ValueCallback<String>(){
                    public void onReceiveValue(String result){System.err.println("SDWEBPROBE=js|result="+result);}
                });
            }
            @Override public void onReceivedError(WebView v,int code,String message,String url){System.err.println("SDWEBPROBE=error|code="+code+"|message="+message);
                if(!retried){retried=true;new Handler().postDelayed(new Runnable(){public void run(){loadPage();}},600);}}
        });
        loadPage();
        System.err.println("SDWEBPROBE=created|javascript=true");
    }
    void loadPage() {
        web.loadDataWithBaseURL("https://saidroid.invalid/","<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0;background:white'><div style='height:50vh;background:#0b3d91;color:white;font-size:7vw'>Android WebView</div><div style='height:50vh;background:#b5651d;color:white;font-size:7vw' id='result'></div><canvas id='c' style='display:block;width:100vw;height:50vh' width='1080' height='1100'></canvas><script>document.getElementById('result').textContent='JavaScript: '+7*6;document.title='JS='+7*6;var c=document.getElementById('c').getContext('2d');c.fillStyle='#00aa55';c.fillRect(0,0,1080,1100);addEventListener('touchstart',function(e){window.lastTouch={x:e.touches[0].clientX,y:e.touches[0].clientY};document.title='touch='+Math.round(e.touches[0].clientX)+','+Math.round(e.touches[0].clientY)});addEventListener('scroll',function(){document.title='scrollY='+Math.round(scrollY)});</script></body></html>","text/html","UTF-8",null);
    }
    @Override public boolean dispatchTouchEvent(android.view.MotionEvent event) {
        boolean handled=super.dispatchTouchEvent(event);
        if(event.getActionMasked()==android.view.MotionEvent.ACTION_UP)new Handler().postDelayed(new Runnable(){public void run(){
            web.evaluateJavascript("JSON.stringify({touch:window.lastTouch,dpr:devicePixelRatio,scroll:scrollY})",new ValueCallback<String>(){
                public void onReceiveValue(String result){
                    try{
                        Object decoded=new org.json.JSONTokener(result).nextValue();
                        org.json.JSONObject state=new org.json.JSONObject(String.valueOf(decoded));
                        org.json.JSONObject touch=state.getJSONObject("touch");
                        System.err.println("SDWEBPROBE=input_state|x="+Math.round(touch.getDouble("x"))+"|y="+Math.round(touch.getDouble("y"))+"|dpr="+state.getDouble("dpr")+"|scroll="+state.getDouble("scroll"));
                    }catch(Exception failure){System.err.println("SDWEBPROBE=input_state_failed|"+failure.getClass().getSimpleName());}
                }
            });
        }},400);
        return handled;
    }
    @Override public void onDestroy(){if(web!=null)web.destroy();super.onDestroy();System.err.println("SDWEBPROBE=destroyed");}
}
