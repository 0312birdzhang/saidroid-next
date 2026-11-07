import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import java.util.HashMap;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;

/** Runtime-local Android settings; never writes Sailfish system settings. */
public final class SdSettingsProvider extends ContentProvider {
    private final HashMap<String,String> values=new HashMap<String,String>();
    @Override public boolean onCreate(){
        values.put("system/font_scale",Float.toString(getContext().getResources().getConfiguration().fontScale));
        values.put("global/animator_duration_scale","1.0");values.put("global/window_animation_scale","1.0");values.put("global/transition_animation_scale","1.0");
        values.put("system/sound_effects_enabled","0"); // No host sound-effect producer is advertised.
        values.put("secure/accessibility_enabled","0"); // No Android accessibility service is installed.
        return true;
    }
    private synchronized String get(String table,String name){
        if(table.equals("secure")&&name.equals("android_id")){
            String current=values.get("secure/android_id");if(current!=null)return current;
            File file=new File(System.getProperty("saidroid.settings.directory","/home/art/data/settings"),"android-id");
            try{
                file.getParentFile().mkdirs();
                if(file.isFile()){try(FileInputStream input=new FileInputStream(file)){byte[] raw=new byte[16];if(input.read(raw)==16)current=new String(raw,"US-ASCII");}}
                if(current==null){byte[] random=new byte[8];new java.security.SecureRandom().nextBytes(random);StringBuilder text=new StringBuilder();for(byte b:random)text.append(String.format(java.util.Locale.US,"%02x",b&255));current=text.toString();try(FileOutputStream output=new FileOutputStream(file)){output.write(current.getBytes("US-ASCII"));}}
                values.put("secure/android_id",current);return current;
            }catch(java.io.IOException failure){throw new IllegalStateException("Cannot persist Android runtime identity",failure);}
        }
        return values.get(table+"/"+name);
    }
    private void enforceWrite(){getContext().enforceCallingOrSelfPermission("android.permission.WRITE_SETTINGS","Writing Android runtime settings requires authorization");}
    @Override public synchronized Bundle call(String method,String argument,Bundle extras){
        if(method.startsWith("GET_")){Bundle result=new Bundle();result.putString("value",get(method.substring(4),argument));return result;}
        if(method.startsWith("PUT_")){enforceWrite();String value=extras==null?null:extras.getString("value");String key=method.substring(4)+"/"+argument;String previous=value==null?values.remove(key):values.put(key,value);
            if(!java.util.Objects.equals(previous,value))getContext().getContentResolver().notifyChange(Uri.parse("content://settings/"+key),null,false);
            return new Bundle();}
        throw new UnsupportedOperationException("Settings operation: "+method);
    }
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] args,String order){
        String table=uri.getPathSegments().isEmpty()?"system":uri.getPathSegments().get(0);
        String name=uri.getPathSegments().size()>1?uri.getLastPathSegment():(args!=null&&args.length>0?args[0]:null);
        String[] columns=projection==null?new String[]{"name","value"}:projection;MatrixCursor cursor=new MatrixCursor(columns);
        if(name!=null){String value=get(table,name);if(value!=null){Object[] row=new Object[columns.length];for(int i=0;i<columns.length;i++){if(columns[i].equals("name"))row[i]=name;else if(columns[i].equals("value"))row[i]=value;else if(columns[i].equals("_id"))row[i]=name.hashCode()&0x7fffffff;else throw new IllegalArgumentException("Unknown settings column");}cursor.addRow(row);}}
        return cursor;
    }
    @Override public String getType(Uri uri){return "vnd.android.cursor.item/name_value";}
    @Override public Uri insert(Uri uri,ContentValues values){enforceWrite();throw new UnsupportedOperationException("Use the settings call API");}
    @Override public int update(Uri uri,ContentValues values,String where,String[] args){enforceWrite();throw new UnsupportedOperationException("Use the settings call API");}
    @Override public int delete(Uri uri,String where,String[] args){enforceWrite();throw new UnsupportedOperationException("Use the settings call API");}
}
