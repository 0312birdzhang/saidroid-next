import android.app.DownloadManager;
import android.content.*;
import android.database.Cursor;
import android.database.sqlite.*;
import android.net.Uri;
import android.os.*;
import android.os.Process;
import android.provider.Downloads;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/** App-owned downloads with actual HTTP/TLS, persisted metadata and private bytes.
 * Supports ordinary cache downloads only. No global system download inventory,
 * external destination, permission grant, notification daemon or fake completion.
 */
public final class SdDownloadsProvider extends ContentProvider {
    private static final String TABLE="downloads";
    private static final long MAX_BYTES=256L*1024*1024;
    private final Map<Long,Job> jobs=new HashMap<Long,Job>();
    private final ThreadPoolExecutor workers=new ThreadPoolExecutor(2,2,0L,TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<Runnable>(16),new ThreadFactory(){public Thread newThread(Runnable task){Thread thread=new Thread(task,"SailDroidDownload");thread.setDaemon(true);return thread;}},new ThreadPoolExecutor.AbortPolicy());
    private SQLiteDatabase database;
    private File directory;
    private final HashMap<String,String> projection=new HashMap<String,String>();
    private static final String[] COLUMNS={"_id","uri","title","description","mimetype","destination","hint","status","lastmod","total_bytes","current_bytes","_data","deleted","is_visible_in_downloads_ui","allow_write","mediaprovider_uri","errorMsg"};
    @Override public boolean onCreate(){
        try {
            File app=new File(SdApkPackage.DATA).getCanonicalFile();
            directory=new File(getContext().getFilesDir(),"downloads");
            if(!directory.getCanonicalPath().startsWith(app.getPath()+File.separator)||!directory.getAbsoluteFile().equals(directory.getCanonicalFile()))throw new SecurityException("Download directory escaped application data");
            if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("Cannot create private download directory");
            database=new SQLiteOpenHelper(getContext(),"saildroid-downloads.db",null,1){
                @Override public void onCreate(SQLiteDatabase db){db.execSQL("CREATE TABLE downloads (_id INTEGER PRIMARY KEY AUTOINCREMENT,uri TEXT NOT NULL,title TEXT,description TEXT,mimetype TEXT,destination INTEGER NOT NULL,hint TEXT,status INTEGER NOT NULL,lastmod INTEGER NOT NULL,total_bytes INTEGER NOT NULL DEFAULT -1,current_bytes INTEGER NOT NULL DEFAULT 0,_data TEXT,deleted INTEGER NOT NULL DEFAULT 0,is_visible_in_downloads_ui INTEGER NOT NULL DEFAULT 0,allow_write INTEGER NOT NULL DEFAULT 0,mediaprovider_uri TEXT,errorMsg TEXT)");}
                @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){throw new IllegalStateException("Unknown downloads schema upgrade");}
            }.getWritableDatabase();
            // A previous process may have exited mid-transfer. Report that real
            // interruption; do not turn a partial file into a successful row.
            ContentValues interrupted=new ContentValues();interrupted.put("status",Downloads.Impl.STATUS_HTTP_DATA_ERROR);interrupted.put("errorMsg","Application process ended during download");
            database.update(TABLE,interrupted,"status IN (?,?)",new String[]{Integer.toString(Downloads.Impl.STATUS_PENDING),Integer.toString(Downloads.Impl.STATUS_RUNNING)});
            for(String column:COLUMNS)projection.put(column,column);
            projection.put(DownloadManager.COLUMN_LOCAL_FILENAME,"_data AS local_filename");
            projection.put(DownloadManager.COLUMN_MEDIA_TYPE,"mimetype AS media_type");
            projection.put(DownloadManager.COLUMN_TOTAL_SIZE_BYTES,"total_bytes AS total_size");
            projection.put(DownloadManager.COLUMN_LAST_MODIFIED_TIMESTAMP,"lastmod AS last_modified_timestamp");
            projection.put(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR,"current_bytes AS bytes_so_far");
            projection.put(DownloadManager.COLUMN_LOCAL_URI,"NULL AS local_uri");
            projection.put(DownloadManager.COLUMN_REASON,"0 AS reason");
            // API29 DownloadManager supplies these exact, fixed SQL aliases.
            // Accept only the known projection entries; arbitrary expressions
            // remain rejected by SQLiteQueryBuilder's strict projection map.
            for(String expression:new ArrayList<String>(projection.values()))projection.put(expression,expression);
            projection.put("'placeholder' AS local_uri","NULL AS local_uri");
            projection.put("'placeholder' AS reason","0 AS reason");
            return true;
        }catch(IOException failure){throw new IllegalStateException("Private downloads storage unavailable",failure);}
    }
    private void authority(Uri uri){
        if(!"downloads".equals(uri.getAuthority())||uri.getPathSegments().isEmpty()||!(uri.getPathSegments().get(0).equals("my_downloads")||uri.getPathSegments().get(0).equals("all_downloads")))throw new IllegalArgumentException("Unsupported downloads URI");
        if(uri.getPathSegments().size()>2)throw new UnsupportedOperationException("Download headers/provider subpaths are unavailable");
        if(Binder.getCallingUid()!=Process.myUid())throw new SecurityException("Foreign UID download access unavailable");
    }
    private Long item(Uri uri){authority(uri);return uri.getPathSegments().size()==2?ContentUris.parseId(uri):null;}
    private String where(Uri uri,String selection){Long id=item(uri);return id==null?selection:"_id="+id+(selection==null?"":" AND ("+selection+")");}
    private static String text(ContentValues values,String name){String value=values.getAsString(name);if(value!=null&&value.length()>8192)throw new IllegalArgumentException("Download field exceeds limit: "+name);return value;}
    @Override public synchronized Uri insert(Uri uri,ContentValues values){
        if(item(uri)!=null)throw new IllegalArgumentException("Insert requires a downloads collection");
        if(!getContext().getPackageName().equals(values.getAsString(Downloads.Impl.COLUMN_NOTIFICATION_PACKAGE)))throw new SecurityException("Download owner package differs");
        getContext().enforceCallingOrSelfPermission("android.permission.INTERNET","Download requires INTERNET");
        Integer destination=values.getAsInteger(Downloads.Impl.COLUMN_DESTINATION);
        if(destination==null||destination!=Downloads.Impl.DESTINATION_CACHE_PARTITION_PURGEABLE)throw new UnsupportedOperationException("Only private default cache downloads are supported");
        Uri source=Uri.parse(text(values,Downloads.Impl.COLUMN_URI));
        if(!(source.getScheme().equals("http")||source.getScheme().equals("https"))||source.getHost()==null||source.getUserInfo()!=null)throw new IllegalArgumentException("Download requires an HTTP(S) URL without embedded credentials");
        if(Boolean.FALSE.equals(values.getAsBoolean(Downloads.Impl.COLUMN_ALLOW_METERED))||values.getAsInteger(Downloads.Impl.COLUMN_FLAGS)!=null&&values.getAsInteger(Downloads.Impl.COLUMN_FLAGS)!=0)throw new UnsupportedOperationException("Requested download scheduling constraints are unavailable");
        Integer networks=values.getAsInteger(Downloads.Impl.COLUMN_ALLOWED_NETWORK_TYPES);
        if(networks!=null&&networks!=-1||Boolean.FALSE.equals(values.getAsBoolean(Downloads.Impl.COLUMN_ALLOW_ROAMING)))throw new UnsupportedOperationException("Requested download network restrictions are unavailable");
        Map<String,String> headers=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);
        for(String key:values.keySet())if(key.startsWith(Downloads.Impl.RequestHeaders.INSERT_KEY_PREFIX)){
            String line=text(values,key);int colon=line==null?-1:line.indexOf(':');
            if(colon<=0||line.indexOf('\r')>=0||line.indexOf('\n')>=0)throw new IllegalArgumentException("Invalid download request header");
            headers.put(line.substring(0,colon).trim(),line.substring(colon+1).trim());
        }
        ContentValues row=new ContentValues();row.put("uri",source.toString());row.put("destination",destination);row.put("status",Downloads.Impl.STATUS_PENDING);row.put("lastmod",System.currentTimeMillis());
        for(String key:new String[]{"title","description","mimetype"})if(values.containsKey(key))row.put(key,text(values,key));
        long id=database.insertOrThrow(TABLE,null,row);Job job=new Job(id,source,headers);jobs.put(id,job);
        try{job.future=workers.submit(job);}catch(RejectedExecutionException full){jobs.remove(id);database.delete(TABLE,"_id=?",new String[]{Long.toString(id)});throw new IllegalStateException("Download queue is full",full);}
        System.err.println("SDDOWNLOAD=queued|id="+id+"|owner="+SdApkPackage.NAME+"|storage=private-cache");
        return ContentUris.withAppendedId(Downloads.Impl.CONTENT_URI,id);
    }
    @Override public synchronized Cursor query(Uri uri,String[] columns,String selection,String[] args,String order){
        authority(uri);SQLiteQueryBuilder query=new SQLiteQueryBuilder();query.setTables(TABLE);query.setProjectionMap(projection);query.setStrict(true);
        Cursor cursor=query.query(database,columns==null?DownloadManager.UNDERLYING_COLUMNS:columns,where(uri,selection),args,null,null,order);
        cursor.setNotificationUri(getContext().getContentResolver(),uri);return cursor;
    }
    @Override public synchronized int delete(Uri uri,String selection,String[] args){
        String clause=where(uri,selection);ArrayList<Long> ids=new ArrayList<Long>();
        try(Cursor rows=database.query(TABLE,new String[]{"_id"},clause,args,null,null,null)){while(rows.moveToNext())ids.add(rows.getLong(0));}
        for(long id:ids){Job job=jobs.remove(id);if(job!=null)job.cancel();privateFile(id,false).delete();privateFile(id,true).delete();}
        int removed=database.delete(TABLE,clause,args);getContext().getContentResolver().notifyChange(uri,null,false);return removed;
    }
    @Override public int update(Uri uri,ContentValues values,String where,String[] args){authority(uri);throw new UnsupportedOperationException("Download control/update is unavailable");}
    @Override public synchronized String getType(Uri uri){Long id=item(uri);if(id==null)return "vnd.android.cursor.dir/download";try(Cursor row=database.query(TABLE,new String[]{"mimetype"},"_id=?",new String[]{id.toString()},null,null,null)){return row.moveToFirst()&&row.getString(0)!=null?row.getString(0):"application/octet-stream";}}
    private File privateFile(long id,boolean partial){
        File path=new File(directory,Long.toString(id)+(partial?".partial":".download"));
        try{if(!path.getCanonicalFile().equals(path.getAbsoluteFile()))throw new SecurityException("Download file is an unexpected link");}catch(IOException failure){throw new IllegalStateException(failure);}
        return path;
    }
    @Override public synchronized ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
        Long id=item(uri);if(id==null||!"r".equals(mode))throw new FileNotFoundException("Only completed download reads are supported");
        try(Cursor row=database.query(TABLE,new String[]{"status"},"_id=?",new String[]{id.toString()},null,null,null)){
            if(!row.moveToFirst()||row.getInt(0)!=Downloads.Impl.STATUS_SUCCESS)throw new FileNotFoundException("Download is not complete");
        }
        return ParcelFileDescriptor.open(privateFile(id,false),ParcelFileDescriptor.MODE_READ_ONLY);
    }
    private final class Job implements Runnable {
        final long id;final Uri source;final Map<String,String> headers;volatile boolean cancelled;volatile HttpURLConnection connection;Future<?> future;
        Job(long id,Uri source,Map<String,String> headers){this.id=id;this.source=source;this.headers=headers;}
        void cancel(){cancelled=true;HttpURLConnection current=connection;if(current!=null)current.disconnect();if(future!=null)future.cancel(true);}
        private void active()throws InterruptedIOException{if(cancelled||Thread.currentThread().isInterrupted())throw new InterruptedIOException("Download cancelled");}
        private void change(ContentValues values){synchronized(SdDownloadsProvider.this){if(jobs.get(id)==this&&!cancelled){values.put("lastmod",System.currentTimeMillis());database.update(TABLE,values,"_id=?",new String[]{Long.toString(id)});}}}
        @Override public void run(){
            File temporary=privateFile(id,true),completed=privateFile(id,false);long bytes=0,total=-1;int status=Downloads.Impl.STATUS_HTTP_DATA_ERROR;String error=null;
            try {
                ContentValues running=new ContentValues();running.put("status",Downloads.Impl.STATUS_RUNNING);change(running);
                URL url=new URL(source.toString());
                for(int redirects=0;;redirects++){
                    active();
                    if(url.getProtocol().equals("http")&&!android.security.NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted(url.getHost()))throw new IOException("Cleartext traffic is not permitted by application policy");
                    connection=(HttpURLConnection)url.openConnection();connection.setConnectTimeout(15000);connection.setReadTimeout(15000);connection.setInstanceFollowRedirects(false);
                    for(Map.Entry<String,String> header:headers.entrySet())connection.setRequestProperty(header.getKey(),header.getValue());
                    int response=connection.getResponseCode();
                    if(response==301||response==302||response==303||response==307||response==308){
                        if(redirects>=5)throw new IOException("Too many download redirects");
                        String location=connection.getHeaderField("Location");if(location==null)throw new IOException("Download redirect has no Location");
                        URL next=new URL(url,location);if(!(next.getProtocol().equals("http")||next.getProtocol().equals("https"))||next.getUserInfo()!=null||url.getProtocol().equals("https")&&!next.getProtocol().equals("https"))throw new IOException("Unsafe download redirect");
                        if(!next.getHost().equalsIgnoreCase(url.getHost())){headers.remove("Authorization");headers.remove("Cookie");}
                        connection.disconnect();url=next;continue;
                    }
                    if(response!=200){status=response>=400&&response<600?response:Downloads.Impl.STATUS_UNHANDLED_HTTP_CODE;throw new IOException("HTTP response "+response);}
                    total=connection.getContentLengthLong();if(total>MAX_BYTES)throw new IOException("Download exceeds private storage limit");
                    ContentValues metadata=new ContentValues();metadata.put("total_bytes",total);metadata.put("mimetype",connection.getContentType());change(metadata);
                    try(InputStream input=connection.getInputStream();FileOutputStream output=new FileOutputStream(temporary)){
                        byte[] buffer=new byte[32768];int count;
                        while((count=input.read(buffer))!=-1){active();bytes+=count;if(bytes>MAX_BYTES)throw new IOException("Download exceeds private storage limit");output.write(buffer,0,count);}
                        output.getFD().sync();
                    }
                    active();if(total>=0&&total!=bytes)throw new EOFException("Download length differs from Content-Length");
                    synchronized(SdDownloadsProvider.this){active();if(jobs.get(id)!=this)throw new InterruptedIOException("Download no longer exists");if(completed.exists()||!temporary.renameTo(completed))throw new IOException("Cannot publish completed download");}
                    status=Downloads.Impl.STATUS_SUCCESS;break;
                }
            }catch(Exception failure){error=failure.getClass().getSimpleName();if(status==Downloads.Impl.STATUS_SUCCESS)status=Downloads.Impl.STATUS_HTTP_DATA_ERROR;}
            finally {
                if(connection!=null)connection.disconnect();temporary.delete();
                synchronized(SdDownloadsProvider.this){
                    if(jobs.get(id)==this&&!cancelled){
                        ContentValues result=new ContentValues();result.put("status",status);result.put("current_bytes",bytes);result.put("total_bytes",total);result.put("lastmod",System.currentTimeMillis());result.put("errorMsg",error);if(status==Downloads.Impl.STATUS_SUCCESS)result.put("_data",completed.getAbsolutePath());
                        database.update(TABLE,result,"_id=?",new String[]{Long.toString(id)});jobs.remove(id);
                        getContext().getContentResolver().notifyChange(ContentUris.withAppendedId(Downloads.Impl.CONTENT_URI,id),null,false);
                        Intent done=new Intent(DownloadManager.ACTION_DOWNLOAD_COMPLETE).setPackage(SdApkPackage.NAME).putExtra(DownloadManager.EXTRA_DOWNLOAD_ID,id);getContext().sendBroadcast(done);
                        System.err.println("SDDOWNLOAD=completed|id="+id+"|status="+status+"|bytes="+bytes+"|error="+error+"|real_io=true");
                    }
                }
            }
        }
    }
}
