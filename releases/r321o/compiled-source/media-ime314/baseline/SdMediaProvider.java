import android.app.ActivityThread;
import android.content.*;
import android.database.Cursor;
import android.database.sqlite.*;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.*;
import android.webkit.MimeTypeMap;
import java.io.*;
import java.util.*;

/** Read-only media inventory of real user Pictures/Videos and private shared media. */
public final class SdMediaProvider extends ContentProvider {
    private SQLiteDatabase db;
    private final HashMap<String,String> projection=new HashMap<String,String>();
    private final ArrayList<File> roots=new ArrayList<File>();
    private static final String[] COLUMNS={"_id","_data","_display_name","_size","mime_type","title","date_added","date_modified","datetaken","width","height","orientation","duration","bucket_id","bucket_display_name","media_type","is_pending","is_favorite","relative_path","volume_name"};
    @Override public boolean onCreate(){
        db=SQLiteDatabase.create(null);
        db.execSQL("CREATE TABLE media (_id INTEGER PRIMARY KEY,_data TEXT UNIQUE,_display_name TEXT,_size INTEGER,mime_type TEXT,title TEXT,date_added INTEGER,date_modified INTEGER,datetaken INTEGER,width INTEGER,height INTEGER,orientation INTEGER,duration INTEGER,bucket_id INTEGER,bucket_display_name TEXT,media_type INTEGER,is_pending INTEGER DEFAULT 0,is_favorite INTEGER DEFAULT 0,relative_path TEXT,volume_name TEXT)");
        for(String name:COLUMNS)projection.put(name,name);
        // API29 location columns are redacted without ACCESS_MEDIA_LOCATION.
        projection.put("latitude","NULL AS latitude");projection.put("longitude","NULL AS longitude");
        projection.put("COUNT(*)","COUNT(*)");projection.put("count(*)","count(*)");
        try{
            String home=System.getenv("HOME"),shared=System.getenv("EXTERNAL_STORAGE");
            if(home==null||shared==null)throw new IllegalStateException("Media roots are not configured");
            for(File root:new File[]{new File(home,"Pictures"),new File(home,"Videos"),new File(shared,"Pictures"),new File(shared,"DCIM"),new File(shared,"Movies")}){
                if(root.isDirectory()&&root.getAbsoluteFile().equals(root.getCanonicalFile())&&!roots.contains(root))roots.add(root);
            }
            db.beginTransaction();int count=0;
            try{HashSet<String> seen=new HashSet<String>();for(File root:roots)count+=scan(root,root,seen,0);db.setTransactionSuccessful();}finally{db.endTransaction();}
            System.err.println("SDMEDIASTORE=indexed|files="+count+"|roots="+roots.size()+"|mode=real-media-read-only");
            return true;
        }catch(IOException failure){throw new IllegalStateException("Cannot index host media",failure);}
    }
    private int scan(File root,File folder,Set<String> seen,int depth)throws IOException{
        if(depth>16||seen.size()>=10000)return 0;
        File[] children=folder.listFiles();if(children==null)return 0;int count=0;
        Arrays.sort(children,Comparator.comparing(File::getName));
        for(File file:children){
            if(file.getName().startsWith(".")||!file.getAbsoluteFile().equals(file.getCanonicalFile())||!file.getCanonicalPath().startsWith(root.getCanonicalPath()+File.separator))continue;
            if(file.isDirectory()){count+=scan(root,file,seen,depth+1);continue;}
            if(!file.isFile()||!file.canRead()||!seen.add(file.getCanonicalPath())||seen.size()>10000)continue;
            String name=file.getName();int dot=name.lastIndexOf('.');if(dot<0)continue;
            String extension=name.substring(dot+1).toLowerCase(Locale.ROOT);String mime=MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension);
            int kind=mime!=null&&mime.startsWith("image/")?1:mime!=null&&mime.startsWith("video/")?3:0;if(kind==0)continue;
            long id=file.getCanonicalPath().hashCode()&0x7fffffff;
            ContentValues row=new ContentValues();row.put("_id",id);row.put("_data",file.getCanonicalPath());row.put("_display_name",name);row.put("_size",file.length());row.put("mime_type",mime);row.put("title",name.substring(0,dot));row.put("date_added",file.lastModified()/1000);row.put("date_modified",file.lastModified()/1000);row.put("datetaken",file.lastModified());BitmapFactory.Options size=new BitmapFactory.Options();size.inJustDecodeBounds=true;if(kind==1)BitmapFactory.decodeFile(file.getCanonicalPath(),size);row.put("width",Math.max(0,size.outWidth));row.put("height",Math.max(0,size.outHeight));row.put("orientation",0);row.put("duration",0);row.put("bucket_id",file.getParent().toLowerCase(Locale.ROOT).hashCode());row.put("bucket_display_name",file.getParentFile().getName());row.put("media_type",kind);row.put("relative_path",root.getName()+"/");row.put("volume_name","external_primary");
            db.insertOrThrow("media",null,row);count++;
        }
        return count;
    }
    private void readPermission(){getContext().enforceCallingOrSelfPermission("android.permission.READ_EXTERNAL_STORAGE","Reading media requires explicit authorization");}
    private String uriWhere(Uri uri){
        if(!"media".equals(uri.getAuthority()))throw new IllegalArgumentException("Unknown media authority");
        List<String> path=uri.getPathSegments();
        if(path.size()<2||!(path.get(0).equals("external")||path.get(0).equals("external_primary")))throw new IllegalArgumentException("Unsupported media volume");
        String where;
        if(path.get(1).equals("images")&&path.size()>=3&&path.get(2).equals("media"))where="media_type=1";
        else if(path.get(1).equals("video")&&path.size()>=3&&path.get(2).equals("media"))where="media_type=3";
        else if(path.get(1).equals("file"))where="1";
        else throw new UnsupportedOperationException("Unsupported MediaStore collection");
        int collection=path.get(1).equals("file")?2:3;
        if(path.size()==collection+1)where+=" AND _id="+ContentUris.parseId(uri);
        else if(path.size()!=collection)throw new IllegalArgumentException("Unsupported media subpath");
        return where;
    }
    @Override public synchronized Cursor query(Uri uri,String[] columns,String selection,String[] args,String order){
        System.err.println("SDMEDIASTORE=query_requested|uri="+uri+"|columns="+Arrays.toString(columns)+"|selection="+selection+"|order="+order);
        readPermission();String where=uriWhere(uri);SQLiteQueryBuilder query=new SQLiteQueryBuilder();query.setTables("media");query.setProjectionMap(projection);query.setStrict(true);query.appendWhere(where);
        String limit=uri.getQueryParameter("limit");if(limit!=null){if(!limit.matches("[0-9]{1,10}(,[0-9]{1,10})?"))throw new IllegalArgumentException("Invalid media limit");for(String value:limit.split(","))if(Long.parseLong(value)>Integer.MAX_VALUE)throw new IllegalArgumentException("Media limit exceeds API29 bounds");}
        Cursor result=query.query(db,columns==null?COLUMNS:columns,selection,args,null,null,order,limit);
        System.err.println("SDMEDIASTORE=query|collection="+uri.getPathSegments().get(1)+"|columns="+Arrays.toString(columns)+"|rows="+result.getCount());return result;
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
        readPermission();if(!"r".equals(mode))throw new FileNotFoundException("Host media provider is read-only");
        String where=uriWhere(uri);if(uri.getLastPathSegment().equals("media")||uri.getLastPathSegment().equals("file"))throw new FileNotFoundException("Media item URI required");
        try(Cursor result=db.query("media",new String[]{"_data"},where,null,null,null,null)){
            if(!result.moveToFirst())throw new FileNotFoundException("Unknown media item");
            File path=new File(result.getString(0));
            try{if(!path.getAbsoluteFile().equals(path.getCanonicalFile()))throw new FileNotFoundException("Media path changed");boolean allowed=false;for(File root:roots)allowed|=path.getCanonicalPath().startsWith(root.getCanonicalPath()+File.separator);if(!allowed)throw new FileNotFoundException("Outside media roots");}catch(IOException failure){throw new FileNotFoundException("Media file is unavailable");}
            return ParcelFileDescriptor.open(path,ParcelFileDescriptor.MODE_READ_ONLY);
        }
    }
    @Override public String getType(Uri uri){readPermission();try(Cursor row=db.query("media",new String[]{"mime_type"},uriWhere(uri),null,null,null,null)){return row.moveToFirst()?row.getString(0):null;}}
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException("Host media insertion is unavailable");}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] args){throw new UnsupportedOperationException("Host media editing is unavailable");}
    @Override public int delete(Uri uri,String selection,String[] args){throw new UnsupportedOperationException("Host media deletion is unavailable");}
}
