package org.example.saildroid.webviewprobe;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.*;
import org.json.JSONObject;

/** No-account regression: physical button -> Java bridge -> custom URI -> navigation. */
public final class VerificationProbeActivity extends Activity {
    WebView web;int calls,navigations,finished;
    String origin="http://127.0.0.1:18786";
    final class Bridge {
        @JavascriptInterface public String echo(String value){calls++;System.err.println("SDVERIFY=java_call|count="+calls+"|thread="+Thread.currentThread().getName());return "native:"+value;}
        public String unannotated(){throw new AssertionError("Unannotated method exposed to JS");}
    }
    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);web=new WebView(this);web.setBackgroundColor(0xffffffff);web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);web.getSettings().setJavaScriptCanOpenWindowsAutomatically(true);setContentView(web);
        web.addJavascriptInterface(new Bridge(),"Bridge");
        CookieManager.getInstance().setCookie(origin+"/", "fromAndroid=one; Path=/");
        CookieManager.getInstance().setCookie(origin+"/", "secondCookie=two; Path=/");
        web.setWebChromeClient(new WebChromeClient(){@Override public boolean onJsPrompt(WebView v,String url,String message,String value,JsPromptResult result){if(message.equals("roundtrip")){System.err.println("SDVERIFY=prompt|handled=true");result.confirm("prompt-ok");return true;}return false;}});
        web.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest request){
                String target=request.getUrl().toString();navigations++;
                System.err.println("SDVERIFY=navigation|scheme="+request.getUrl().getScheme()+"|gesture="+request.hasGesture()+"|redirect="+request.isRedirect());
                if(target.startsWith("testbridge:")){web.evaluateJavascript("document.getElementById('result').textContent+='|callback';location.href='/redirect'",null);return true;}return false;
            }
            @Override public void onPageFinished(WebView v,String url){
                System.err.println("SDVERIFY=finished|path="+android.net.Uri.parse(url).getPath()+"|count="+(++finished));
                web.evaluateJavascript("JSON.stringify({text:document.body.innerText,bridge:typeof Bridge.echo,hidden:typeof Bridge.unannotated})",new ValueCallback<String>(){public void onReceiveValue(String state){System.err.println("SDVERIFY=state|"+state);}});
                String cookies=CookieManager.getInstance().getCookie(origin+"/next");
                System.err.println("SDVERIFY=cookies|android="+(cookies!=null&&cookies.contains("fromAndroid=one"))+"|server="+(cookies!=null&&cookies.contains("fromServer=three")));
            }
            @Override public void onReceivedError(WebView v,int code,String message,String url){System.err.println("SDVERIFY=error|code="+code);}
        });
        java.util.Map<String,String> headers=new java.util.HashMap<String,String>();headers.put("X-SD-Test","android-provider");web.loadUrl(origin+"/start",headers);
    }
    @Override public void onDestroy(){if(web!=null)web.destroy();super.onDestroy();System.err.println("SDVERIFY=destroyed|calls="+calls+"|navigations="+navigations);}
}
