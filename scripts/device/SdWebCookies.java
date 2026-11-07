import android.webkit.CookieManager;
import android.webkit.ValueCallback;
import android.webkit.WebView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.net.HttpCookie;
import java.net.URI;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.Map;

/** URL/domain/path-aware Android cookie mirror, synchronized with real WebKit. */
public final class SdWebCookies extends CookieManager {
    public interface Listener { void changed(JSONObject operation); }
    private final Map<String,JSONObject> jar=new LinkedHashMap<String,JSONObject>();
    private final ArrayList<Listener> listeners=new ArrayList<Listener>();
    private final File file;
    private long version;
    private boolean accepted=true;
    private static String key(JSONObject c){return c.optString("domain")+"\n"+c.optString("path")+"\n"+c.optString("name");}
    public SdWebCookies(){
        File directory=new File(System.getProperty("saidroid.data","/home/art/data/shared"),"saidroid-webview");directory.mkdirs();file=new File(directory,"cookie-mirror.json");
        try{if(file.isFile()&&file.length()<2*1024*1024){byte[] bytes=java.nio.file.Files.readAllBytes(file.toPath());JSONArray entries=new JSONArray(new String(bytes,"UTF-8"));for(int i=0;i<entries.length();i++){JSONObject c=entries.getJSONObject(i);if(c.optLong("expires",0)==0||c.optLong("expires")>System.currentTimeMillis()/1000)jar.put(key(c),c);}}}catch(Exception failure){System.err.println("SDWEBVIEW=cookie_store_read_failed|type="+failure.getClass().getSimpleName());}
    }
    public synchronized void attach(Listener listener){listeners.add(listener);}
    public synchronized void detach(Listener listener){listeners.remove(listener);}
    public synchronized JSONObject snapshot(){
        JSONObject operation=new JSONObject();try{JSONArray entries=new JSONArray();for(JSONObject c:jar.values())entries.put(c);operation.put("op","cookies_sync").put("version",version).put("entries",entries);}catch(Exception failure){throw new IllegalStateException(failure);}return operation;
    }
    public synchronized void nativeSnapshot(JSONArray entries,long seenVersion){
        if(seenVersion<version)return;
        jar.clear();for(int i=0;i<entries.length();i++){JSONObject c=entries.optJSONObject(i);if(c!=null)jar.put(key(c),c);}persist();
        System.err.println("SDWEBVIEW=cookies_synchronized|entries="+jar.size());
    }
    private void persist(){
        try{JSONArray entries=new JSONArray();for(JSONObject c:jar.values())entries.put(c);File temp=new File(file.getParentFile(),".cookie-mirror.tmp");try(java.io.FileOutputStream out=new java.io.FileOutputStream(temp)){out.write(entries.toString().getBytes("UTF-8"));}temp.setReadable(false,false);temp.setWritable(false,false);temp.setReadable(true,true);temp.setWritable(true,true);if(!temp.renameTo(file))throw new java.io.IOException("cookie mirror rename failed");}
        catch(Exception failure){System.err.println("SDWEBVIEW=cookie_store_write_failed|type="+failure.getClass().getSimpleName());}
    }
    private void broadcast(JSONObject operation){for(Listener l:new ArrayList<Listener>(listeners))l.changed(operation);}
    public synchronized void setAcceptCookie(boolean value){accepted=value;}
    public synchronized boolean acceptCookie(){return accepted;}
    public void setAcceptThirdPartyCookies(WebView view,boolean value){} // Engine policy remains explicit in settings.
    public boolean acceptThirdPartyCookies(WebView view){return true;}
    public void setCookie(String url,String value){set(url,value);}
    public void setCookie(String url,String value,ValueCallback<Boolean> callback){boolean success=set(url,value);if(callback!=null)callback.onReceiveValue(success);}
    private synchronized boolean set(String url,String value){
        if(!accepted||url==null||value==null)return false;
        try{
            URI uri=new URI(url);String host=uri.getHost();if(host==null)return false;host=host.toLowerCase(java.util.Locale.ROOT);
            String path=uri.getPath();if(path==null||!path.startsWith("/"))path="/";int slash=path.lastIndexOf('/');String defaultPath=slash<=0?"/":path.substring(0,slash);
            // HttpCookie implements obsolete RFC2965 and rejects legal browser cookie
            // names such as "domain" and "secure". Parse attributes with a neutral
            // name, retaining the original validated RFC6265 token for storage.
            int equals=value.indexOf('=');if(equals<=0)return false;
            String name=value.substring(0,equals).trim();
            for(int i=0;i<name.length();i++){char ch=name.charAt(i);if(ch<=32||ch>=127||"()<>@,;:\\\"/[]?={}".indexOf(ch)>=0)return false;}
            if(name.isEmpty())return false;
            for(HttpCookie c:HttpCookie.parse("sd_cookie"+value.substring(equals))){
                String domain=c.getDomain();boolean hostOnly=domain==null;if(hostOnly)domain=host;else{domain=domain.toLowerCase(java.util.Locale.ROOT);while(domain.startsWith("."))domain=domain.substring(1);if(!host.equals(domain)&&!host.endsWith("."+domain))return false;}
                String cookiePath=c.getPath();if(cookiePath==null||!cookiePath.startsWith("/"))cookiePath=defaultPath;
                long expires=c.getMaxAge()<0?0:System.currentTimeMillis()/1000+c.getMaxAge();
                JSONObject item=new JSONObject().put("name",name).put("value",c.getValue()).put("domain",hostOnly?domain:"."+domain).put("path",cookiePath).put("secure",c.getSecure()).put("httpOnly",c.isHttpOnly()).put("expires",expires).put("session",c.getMaxAge()<0);
                if(c.getMaxAge()==0)jar.remove(key(item));else jar.put(key(item),item);
                version++;JSONObject operation=new JSONObject().put("op","cookie_set").put("version",version).put("cookie",item);broadcast(operation);
            }
            persist();return true;
        }catch(Exception failure){System.err.println("SDWEBVIEW=cookie_rejected|type="+failure.getClass().getSimpleName());return false;}
    }
    public synchronized String getCookie(String url){
        try{
            URI uri=new URI(url);String host=uri.getHost();if(host==null)return null;host=host.toLowerCase(java.util.Locale.ROOT);String path=uri.getPath();if(path==null||path.isEmpty())path="/";
            ArrayList<JSONObject> found=new ArrayList<JSONObject>();long now=System.currentTimeMillis()/1000;
            for(JSONObject c:jar.values()){
                String domain=c.optString("domain"),bare=domain.startsWith(".")?domain.substring(1):domain;String cp=c.optString("path","/");
                boolean match=host.equals(bare)||(domain.startsWith(".")&&host.endsWith("."+bare));
                if(!match||(c.optBoolean("secure")&&!"https".equalsIgnoreCase(uri.getScheme()))||(c.optLong("expires")>0&&c.optLong("expires")<=now))continue;
                if(!path.equals(cp)&&!(path.startsWith(cp)&&(cp.endsWith("/")||path.charAt(cp.length())=='/')))continue;
                found.add(c);
            }
            Collections.sort(found,new Comparator<JSONObject>(){public int compare(JSONObject a,JSONObject b){return b.optString("path").length()-a.optString("path").length();}});
            StringBuilder text=new StringBuilder();for(JSONObject c:found){if(text.length()>0)text.append("; ");text.append(c.optString("name")).append('=').append(c.optString("value"));}
            System.err.println("SDWEBVIEW=cookie_get|matches="+found.size());return text.length()==0?null:text.toString();
        }catch(Exception failure){return null;}
    }
    public String getCookie(String url,boolean privateBrowsing){return getCookie(url);}
    private synchronized boolean clear(boolean sessions){
        boolean changed=false;java.util.Iterator<JSONObject> it=jar.values().iterator();while(it.hasNext()){JSONObject c=it.next();if(!sessions||c.optLong("expires")==0){it.remove();changed=true;}}
        version++;persist();try{broadcast(new JSONObject().put("op","cookies_clear").put("sessions",sessions).put("version",version));}catch(Exception ignored){}return changed;
    }
    public void removeSessionCookie(){clear(true);}
    public void removeSessionCookies(ValueCallback<Boolean> callback){boolean changed=clear(true);if(callback!=null)callback.onReceiveValue(changed);}
    public void removeAllCookie(){clear(false);}
    public void removeAllCookies(ValueCallback<Boolean> callback){boolean changed=clear(false);if(callback!=null)callback.onReceiveValue(changed);}
    public synchronized boolean hasCookies(){return !jar.isEmpty();}
    public boolean hasCookies(boolean privateBrowsing){return hasCookies();}
    public synchronized void removeExpiredCookie(){long now=System.currentTimeMillis()/1000;java.util.Iterator<JSONObject> it=jar.values().iterator();while(it.hasNext()){long expiry=it.next().optLong("expires");if(expiry>0&&expiry<=now)it.remove();}persist();}
    public synchronized void flush(){persist();System.err.println("SDWEBVIEW=cookie_flush|entries="+jar.size());}
    protected boolean allowFileSchemeCookiesImpl(){return false;}
    protected void setAcceptFileSchemeCookiesImpl(boolean value){}
}
