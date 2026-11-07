import android.webkit.JavascriptInterface;
import org.json.JSONArray;
import org.json.JSONObject;
import java.lang.reflect.Method;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ThreadFactory;

/** Explicitly registered Android JS interfaces; no unannotated Object methods. */
public final class SdWebInterfaces {
    public interface Reply { void send(JSONObject response); }
    private final Map<String,Object> objects=new LinkedHashMap<String,Object>();
    private final ThreadPoolExecutor worker=new ThreadPoolExecutor(1,1,15,TimeUnit.SECONDS,
        new ArrayBlockingQueue<Runnable>(32),new ThreadFactory(){public Thread newThread(Runnable task){Thread t=new Thread(task,"sd-webview-javabridge");t.setDaemon(true);return t;}});
    public synchronized void add(String name,Object object){
        if(name==null||name.length()>256||object==null)throw new IllegalArgumentException("Invalid JS interface");
        objects.put(name,object);
        System.err.println("SDWEBVIEW=java_interface_registered|name="+name+"|methods="+methods(object).length());
    }
    public synchronized void remove(String name){objects.remove(name);}
    private static JSONArray methods(Object object){
        JSONArray names=new JSONArray();java.util.HashSet<String> seen=new java.util.HashSet<String>();
        for(Method method:object.getClass().getMethods())if(method.isAnnotationPresent(JavascriptInterface.class)&&seen.add(method.getName()))names.put(method.getName());
        return names;
    }
    public synchronized JSONObject description(){
        JSONObject value=new JSONObject();
        try{for(Map.Entry<String,Object> e:objects.entrySet())value.put(e.getKey(),methods(e.getValue()));}catch(Exception failure){throw new IllegalStateException(failure);}
        return value;
    }
    public void call(final JSONObject request,final Reply reply){
        try{worker.execute(new Runnable(){public void run(){
            JSONObject result=new JSONObject();
            try{
                String name=request.getString("name"),member=request.getString("method");JSONArray arguments=request.getJSONArray("args");
                Object object; synchronized(SdWebInterfaces.this){object=objects.get(name);}
                if(object==null||arguments.length()>32)throw new IllegalArgumentException("JS interface unavailable");
                Method selected=null;Object[] values=null;
                for(Method m:object.getClass().getMethods()){
                    if(!m.getName().equals(member)||!m.isAnnotationPresent(JavascriptInterface.class)||m.getParameterTypes().length!=arguments.length())continue;
                    try{Object[] candidate=new Object[arguments.length()];for(int i=0;i<candidate.length;i++)candidate[i]=convert(arguments.opt(i),m.getParameterTypes()[i]);selected=m;values=candidate;break;}
                    catch(IllegalArgumentException mismatch){}
                }
                if(selected==null)throw new NoSuchMethodException("No annotated JS method accepts the arguments");
                selected.setAccessible(true);Object value=selected.invoke(object,values);
                if(value!=null&&!(value instanceof String||value instanceof Number||value instanceof Boolean||value instanceof Character))throw new IllegalArgumentException("Unsupported JS return type");
                result.put("ok",true).put("undefined",selected.getReturnType()==Void.TYPE).put("value",value==null?JSONObject.NULL:value instanceof Character?value.toString():value);
                System.err.println("SDWEBVIEW=java_interface_call|name="+name+"|method="+member+"|handled=true");
            }catch(Throwable failure){try{result.put("ok",false).put("error",failure.getClass().getSimpleName());}catch(Exception ignored){}
                System.err.println("SDWEBVIEW=java_interface_call|handled=false|type="+failure.getClass().getSimpleName());}
            reply.send(result);
        }});}catch(java.util.concurrent.RejectedExecutionException full){
            JSONObject result=new JSONObject();try{result.put("ok",false).put("error","bridge unavailable");}catch(Exception ignored){}reply.send(result);
        }
    }
    private static Object convert(Object value,Class<?> type){
        if(value==JSONObject.NULL)value=null;
        if(type==String.class)return value==null?null:String.valueOf(value);
        if(type==Boolean.TYPE||type==Boolean.class){if(value instanceof Boolean)return value;throw new IllegalArgumentException();}
        if(type==Character.TYPE||type==Character.class){String s=String.valueOf(value);if(s.length()==1)return s.charAt(0);throw new IllegalArgumentException();}
        if(value instanceof Number){Number n=(Number)value;if(type==Integer.TYPE||type==Integer.class)return n.intValue();if(type==Long.TYPE||type==Long.class)return n.longValue();if(type==Float.TYPE||type==Float.class)return n.floatValue();if(type==Double.TYPE||type==Double.class)return n.doubleValue();if(type==Short.TYPE||type==Short.class)return n.shortValue();if(type==Byte.TYPE||type==Byte.class)return n.byteValue();}
        if(value==null&&!type.isPrimitive())return null;
        throw new IllegalArgumentException("Unsupported JS argument");
    }
    public void close(){worker.shutdownNow();synchronized(this){objects.clear();}}
}
