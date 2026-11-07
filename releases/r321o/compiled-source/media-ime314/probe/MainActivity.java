package org.example.saildroid.mediarefresh;
import android.app.Activity;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.*;
import android.net.Uri;
import android.provider.MediaStore;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
import java.io.*;
public final class MainActivity extends Activity {
 private static final String READ="android.permission.READ_EXTERNAL_STORAGE";
 private final Uri collection=MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
 private File image;private EditText editor;
 @Override public void onCreate(Bundle state){super.onCreate(state);
  LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);
  TextView title=new TextView(this);title.setText("Media refresh and keyboard regression");layout.addView(title);
  editor=new EditText(this);editor.setHint("Tap to test keyboard");layout.addView(editor,new LinearLayout.LayoutParams(-1,180));setContentView(layout);
  if(checkSelfPermission(READ)!=PackageManager.PERMISSION_GRANTED){
   try(Cursor c=getContentResolver().query(collection,new String[]{"_id"},null,null,null)){throw new AssertionError("Unauthorized query succeeded");}catch(SecurityException expected){System.err.println("SDMEDIA_REFRESH_PROBE=denied_query_passed");}
   new Handler().postDelayed(()->requestPermissions(new String[]{READ},314),400);
  }else verify();
 }
 @Override public void onRequestPermissionsResult(int code,String[] names,int[] grants){if(code!=314||grants.length!=1||grants[0]!=PackageManager.PERMISSION_GRANTED)throw new AssertionError("Permission not granted");verify();}
 private long query(int width,int height,boolean expected){try(Cursor c=getContentResolver().query(collection,new String[]{"_id","width","height","_size"},"_data=?",new String[]{image.getAbsolutePath()},"date_modified DESC")){
  if(c==null||c.getCount()!=(expected?1:0))throw new AssertionError("Unexpected refreshed row count");if(!expected)return -1;c.moveToFirst();if(c.getInt(1)!=width||c.getInt(2)!=height||c.getLong(3)!=image.length())throw new AssertionError("Stale media dimensions or size");return c.getLong(0);
 }}
 private void write(int w,int h,int color,long stamp)throws IOException{Bitmap bitmap=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);bitmap.eraseColor(color);try(FileOutputStream out=new FileOutputStream(image)){if(!bitmap.compress(Bitmap.CompressFormat.PNG,100,out))throw new AssertionError("PNG failed");}finally{bitmap.recycle();}if(!image.setLastModified(stamp))throw new AssertionError("Timestamp update failed");}
 private void verify(){File folder=new File(System.getenv("EXTERNAL_STORAGE"),"Pictures/SailDroidMediaRefresh314");image=new File(folder,"owned-fixture.png");
  if(folder.exists())throw new AssertionError("Fixture folder already exists");
  try{
   query(0,0,false);if(!folder.mkdirs())throw new AssertionError("Create fixture folder failed");
   write(64,48,Color.RED,1700000000000L);long id=query(64,48,true);Uri item=ContentUris.withAppendedId(collection,id);
   try(InputStream in=getContentResolver().openInputStream(item)){if(in.read()!=137)throw new AssertionError("Open did not return PNG");}
   try{getContentResolver().openFileDescriptor(item,"w");throw new AssertionError("Provider accepted write mode");}catch(FileNotFoundException expected){}
   System.err.println("SDMEDIA_REFRESH_PROBE=new_file_passed|size=64x48|id="+id);
   write(96,72,Color.BLUE,1700000005000L);if(query(96,72,true)!=id)throw new AssertionError("ID changed after edit");System.err.println("SDMEDIA_REFRESH_PROBE=modified_file_passed|size=96x72|stable_id=true");
   if(!image.delete())throw new AssertionError("Delete fixture failed");query(0,0,false);System.err.println("SDMEDIA_REFRESH_PROBE=removed_file_passed");
   if(!folder.delete())throw new AssertionError("Remove fixture folder failed");System.err.println("SDMEDIA_REFRESH_PROBE=flow_passed|new_modified_removed=true|read_only=true");
  }catch(IOException error){throw new AssertionError(error);}finally{if(image.exists())image.delete();if(folder.exists())folder.delete();}
 }
}
