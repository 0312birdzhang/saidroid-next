import com.android.compatibility.common.tradefed.targetprep.DynamicConfigPusher;
import com.android.compatibility.common.util.DynamicConfigHandler;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.lang.reflect.Field;
import org.json.JSONObject;

/** Use the official preparer's endpoint and merge implementation, with bounds. */
public final class PrepareDynamicConfig {
    public static void main(String[] args)throws Exception {
        File input=new File(args[0]);String module=args[1],version=args[2];Path output=Paths.get(args[3]);
        DynamicConfigPusher defaults=new DynamicConfigPusher();
        Field urlField=DynamicConfigPusher.class.getDeclaredField("mConfigUrl");urlField.setAccessible(true);
        Field keyField=DynamicConfigPusher.class.getDeclaredField("mApiKey");keyField.setAccessible(true);
        String template=(String)urlField.get(defaults);
        String address=template.replace("{suite-name}","cts").replace("{module}",module).replace("{version}",version).replace("{api-key}",(String)keyField.get(defaults));
        String remote=null,error=null;int status=0;
        try{
            HttpURLConnection connection=(HttpURLConnection)new URL(address).openConnection();connection.setConnectTimeout(5000);connection.setReadTimeout(5000);status=connection.getResponseCode();
            if(status==200)try(InputStream stream=connection.getInputStream()){
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int count;
                while((count=stream.read(buffer))!=-1){bytes.write(buffer,0,count);if(bytes.size()>4*1024*1024)throw new IOException("Remote configuration exceeds bound");}
                remote=bytes.toString("UTF-8");
            }
            else error="HTTP "+status;
            connection.disconnect();
        }catch(IOException failure){error=failure.getClass().getSimpleName();}
        File merged=DynamicConfigHandler.getMergedDynamicConfigFile(input,remote,module);
        Files.copy(merged.toPath(),output,StandardCopyOption.REPLACE_EXISTING);Files.delete(merged.toPath());
        if(remote!=null)Files.write(Paths.get(args[3]+".remote.json"),remote.getBytes("UTF-8"));
        JSONObject meta=new JSONObject();meta.put("module",module);meta.put("version",version);meta.put("http_status",status);meta.put("remote_retrieved",remote!=null);meta.put("remote_error",error==null?JSONObject.NULL:error);meta.put("merge_implementation","official DynamicConfigHandler");meta.put("endpoint",address.split("\\?",2)[0]);
        Files.write(Paths.get(args[3]+".metadata.json"),meta.toString(2).getBytes("UTF-8"));
    }
}
