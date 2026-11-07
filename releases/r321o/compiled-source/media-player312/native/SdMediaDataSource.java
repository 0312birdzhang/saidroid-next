import android.media.MediaDataSource;
import android.security.NetworkSecurityPolicy;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.ProtocolException;
import java.net.InetAddress;
import java.net.Socket;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SNIHostName;
import java.util.LinkedHashMap;
import java.util.Map;

/** HTTP bytes through the application's Android URLConnection/TLS policy. */
public final class SdMediaDataSource extends MediaDataSource {
    private final URL url;
    private final LinkedHashMap<String,String> headers=new LinkedHashMap<>();
    private HttpURLConnection connection;
    private InputStream input;
    private long position, size=-1;
    private boolean closed;
    private final String tlsHost;
    public SdMediaDataSource(String uri,String[] keys,String[] values)throws IOException {
        url=new URL(uri);
        if(!url.getProtocol().equals("http")&&!url.getProtocol().equals("https"))throw new ProtocolException("Unsupported media protocol");
        if((keys==null)!=(values==null)||(keys!=null&&keys.length!=values.length))throw new IllegalArgumentException("Mismatched media headers");
        if(keys!=null)for(int i=0;i<keys.length;i++) {
            if(keys[i]==null||values[i]==null)throw new IllegalArgumentException("Null media header");
            headers.put(keys[i],values[i]);
        }
        // HTTPDNS clients can supply an IP endpoint plus the real HTTP Host.
        // Use that explicit authority for both SNI and certificate name checking;
        // retain the application's socket factory and certificate trust policy.
        String authority=null;
        for(Map.Entry<String,String> entry:headers.entrySet())if(entry.getKey().equalsIgnoreCase("Host"))authority=entry.getValue();
        String endpoint=url.getHost();
        boolean numeric=endpoint.indexOf(':')>=0||endpoint.matches("[0-9.]+");
        if(numeric&&authority!=null) {
            URL identity=new URL(url.getProtocol()+"://"+authority+"/");
            if(identity.getUserInfo()!=null||!identity.getPath().equals("/")||identity.getQuery()!=null||identity.getRef()!=null||identity.getHost().isEmpty())throw new ProtocolException("Invalid media Host authority");
            tlsHost=identity.getHost();
        } else tlsHost=null;
        System.err.println("SDMEDIA_HTTP=source|headers="+headers.keySet()+"|ip_endpoint="+numeric+"|explicit_tls_identity="+(tlsHost!=null));
    }
    private void disconnect() {
        if(input!=null)try{input.close();}catch(IOException ignored){}
        input=null;if(connection!=null)connection.disconnect();connection=null;
    }
    private void connect(long requested)throws IOException {
        if(closed)throw new IOException("Media data source is closed");
        disconnect();
        if(url.getProtocol().equals("http")&&!NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted(url.getHost()))throw new IOException("Cleartext media is disallowed by the application policy");
        HttpURLConnection next=(HttpURLConnection)url.openConnection();
        if(next instanceof HttpsURLConnection&&tlsHost!=null) {
            HttpsURLConnection secure=(HttpsURLConnection)next;
            final HostnameVerifier verifier=secure.getHostnameVerifier();
            final String endpoint=bareHost(url.getHost()),identity=tlsHost;
            secure.setSSLSocketFactory(new EndpointTlsFactory(secure.getSSLSocketFactory(),endpoint,identity));
            secure.setHostnameVerifier((host,session)->verifier.verify(bareHost(host).equals(endpoint)?identity:host,session));
        }
        next.setConnectTimeout(8000);next.setReadTimeout(8000);next.setInstanceFollowRedirects(true);
        for(Map.Entry<String,String> entry:headers.entrySet())next.setRequestProperty(entry.getKey(),entry.getValue());
        // Byte-addressable media transport must not negotiate compressed HTTP bodies.
        next.setRequestProperty("Accept-Encoding","identity");
        if(requested>0)next.setRequestProperty("Range","bytes="+requested+"-");
        connection=next;
        try {
            int status=next.getResponseCode();
            if(status!=200&&status!=206)throw new IOException("Media HTTP status "+status);
            if(requested>0&&status!=206)throw new ProtocolException("Server ignored media byte range");
            if(status==206) {
                String range=next.getHeaderField("Content-Range");
                if(range==null||!range.startsWith("bytes "))throw new ProtocolException("Missing media Content-Range");
                int dash=range.indexOf('-'),slash=range.indexOf('/');
                try {
                    if(dash<6||slash<dash||Long.parseLong(range.substring(6,dash))!=requested)throw new ProtocolException("Wrong media byte range");
                    String total=range.substring(slash+1);size=total.equals("*")?-1:Long.parseLong(total);
                } catch(NumberFormatException error){throw new ProtocolException("Malformed media Content-Range");}
            } else size=next.getContentLengthLong();
            input=next.getInputStream();position=requested;
            System.err.println("SDMEDIA_HTTP=connected|status="+status+"|offset="+requested+"|size="+size+"|headers="+headers.size()+"|transport=android-urlconnection|tls=application-policy");
        } catch(IOException error){disconnect();throw error;}
    }
    @Override public synchronized int readAt(long at,byte[] data,int offset,int length)throws IOException {
        if(at<0||offset<0||length<0||offset>data.length-length)throw new IllegalArgumentException("Invalid media read range");
        if(length==0)return 0;
        if(closed)throw new IOException("Media data source is closed");
        if(size>=0&&at>=size)return -1;
        if(input==null||at!=position)connect(at);
        int count=input.read(data,offset,length);if(count>0)position+=count;return count;
    }
    @Override public synchronized long getSize()throws IOException {if(closed)throw new IOException("Media data source is closed");if(connection==null)connect(0);return size;}
    @Override public synchronized void close(){if(!closed){closed=true;disconnect();System.err.println("SDMEDIA_HTTP=closed");}}
    private static String bareHost(String host){return host.startsWith("[")&&host.endsWith("]")?host.substring(1,host.length()-1):host;}
    private static final class EndpointTlsFactory extends SSLSocketFactory {
        private final SSLSocketFactory delegate;
        private final String endpoint,identity;
        EndpointTlsFactory(SSLSocketFactory delegate,String endpoint,String identity){this.delegate=delegate;this.endpoint=endpoint;this.identity=identity;}
        @Override public String[] getDefaultCipherSuites(){return delegate.getDefaultCipherSuites();}
        @Override public String[] getSupportedCipherSuites(){return delegate.getSupportedCipherSuites();}
        @Override public Socket createSocket(Socket socket,String host,int port,boolean close)throws IOException{
            boolean explicit=bareHost(host).equals(endpoint);
            Socket result=delegate.createSocket(socket,explicit?identity:host,port,close);
            if(explicit&&result instanceof SSLSocket&&identity.indexOf(':')<0&&!identity.matches("[0-9.]+")) {
                SSLSocket secure=(SSLSocket)result;SSLParameters parameters=secure.getSSLParameters();
                parameters.setServerNames(java.util.Collections.singletonList(new SNIHostName(identity)));secure.setSSLParameters(parameters);
            }
            return result;
        }
        @Override public Socket createSocket(String host,int port)throws IOException{return delegate.createSocket(host,port);}
        @Override public Socket createSocket(String host,int port,InetAddress local,int localPort)throws IOException{return delegate.createSocket(host,port,local,localPort);}
        @Override public Socket createSocket(InetAddress host,int port)throws IOException{return delegate.createSocket(host,port);}
        @Override public Socket createSocket(InetAddress host,int port,InetAddress local,int localPort)throws IOException{return delegate.createSocket(host,port,local,localPort);}
    }
}
