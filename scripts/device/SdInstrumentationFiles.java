import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.FileNotFoundException;

/** Read-only Tradefed configuration-file transport for a prepared test run. */
public final class SdInstrumentationFiles extends ContentProvider {
    @Override public boolean onCreate(){return true;}
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException {
        if(!SdInstrumentation.requested()||!"r".equals(mode)||!"android.tradefed.contentprovider".equals(uri.getAuthority())||uri.getPath()==null||uri.getPath().contains("/../"))throw new FileNotFoundException("Only prepared read-only instrumentation configuration is available");
        return ParcelFileDescriptor.open(SdInstrumentation.dynamicConfig(uri.getLastPathSegment()),ParcelFileDescriptor.MODE_READ_ONLY);
    }
    @Override public String getType(Uri uri){return "application/xml";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] arguments,String order){throw new UnsupportedOperationException("Read-only configuration files");}
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException("Read-only configuration files");}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] arguments){throw new UnsupportedOperationException("Read-only configuration files");}
    @Override public int delete(Uri uri,String selection,String[] arguments){throw new UnsupportedOperationException("Read-only configuration files");}
}
