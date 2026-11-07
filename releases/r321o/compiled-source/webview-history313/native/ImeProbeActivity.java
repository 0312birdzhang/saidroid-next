package org.example.saildroid.webviewprobe;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import org.json.JSONObject;
import org.json.JSONTokener;

/** An ordinary local form: only real keyboard events may change its value. */
public final class ImeProbeActivity extends Activity {
    WebView web;Handler handler=new Handler();String previous="";boolean closed;
    final Runnable poll=new Runnable(){public void run(){if(closed)return;web.evaluateJavascript("JSON.stringify({id:document.activeElement.id,value:document.getElementById('plain').value,passwordLength:document.getElementById('secret').value.length,events:window.inputEvents||0,trusted:window.trustedInputs||0})",new ValueCallback<String>(){public void onReceiveValue(String result){try{
        JSONObject state=new JSONObject(String.valueOf(new JSONTokener(result).nextValue()));String audit=state.toString();if(!audit.equals(previous)){previous=audit;System.err.println("WEB_IME_PROBE=state|"+audit);}
    }catch(Exception ignored){}}});handler.postDelayed(this,300);}};
    @Override public void onCreate(Bundle state){super.onCreate(state);web=new WebView(this);setContentView(web);web.getSettings().setJavaScriptEnabled(true);web.setWebViewClient(new WebViewClient(){public void onPageFinished(WebView v,String url){System.err.println("WEB_IME_PROBE=loaded");handler.post(poll);}});
        web.loadDataWithBaseURL("https://saidroid.invalid/ime/","<!doctype html><meta name='viewport' content='width=device-width,initial-scale=1'><style>body{background:#eef4fa;font:24px sans-serif;margin:0}h1{font-size:24px;margin:18px}input{position:absolute;left:8vw;width:80vw;height:9vh;font:24px sans-serif;border:2px solid #246;border-radius:12px}#plain{top:12vh}#secret{top:30vh}#phone{top:39vh}button{position:absolute;left:8vw;top:50vh;width:80vw;height:10vh;font:24px sans-serif}</style><h1>Real WebView keyboard</h1><input id='plain' autocomplete='off' placeholder='Plain text'><input id='secret' type='password' autocomplete='off' placeholder='Password'><input id='phone' type='tel' autocomplete='off' placeholder='Phone'><button id='blur' onclick='document.activeElement.blur();this.focus()'>Finish editing</button><script>window.inputEvents=0;window.trustedInputs=0;addEventListener('input',function(e){inputEvents++;if(e.isTrusted)trustedInputs++});</script>","text/html","UTF-8",null);
    }
    @Override public void onDestroy(){closed=true;handler.removeCallbacksAndMessages(null);web.destroy();super.onDestroy();}
}
