import android.os.*;
import android.os.Process;
import android.os.storage.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;

/** Private application storage backed by real user-owned Linux directories. */
public final class SdStorageManager implements InvocationHandler {
    private static final SdStorageManager instance=new SdStorageManager();
    private final Binder binder=new Binder();private final IStorageManager service;
    private final Set<IBinder> listeners=new HashSet<IBinder>();
    private SdStorageManager(){service=(IStorageManager)Proxy.newProxyInstance(IStorageManager.class.getClassLoader(),new Class<?>[]{IStorageManager.class},this);binder.attachInterface(service,"android.os.storage.IStorageManager");}
    public static IBinder binder(){return instance.binder;}
    private static File storage(){String value=System.getenv("EXTERNAL_STORAGE");if(value==null)throw new IllegalStateException("Private external storage not configured");File path=new File(value);if(!path.isDirectory()||!path.canRead())throw new IllegalStateException("Private storage unavailable");return path;}
    private static StorageVolume volume(){File path=storage();return new StorageVolume("saildroid:private",path,path,"SailDroid",true,false,true,false,0,new UserHandle(Process.myUserHandle().getIdentifier()),null,path.canWrite()?Environment.MEDIA_MOUNTED:Environment.MEDIA_MOUNTED_READ_ONLY);}
    @Override public Object invoke(Object proxy,Method method,Object[] a)throws Exception{
        String n=method.getName();if(n.equals("asBinder"))return binder;if(n.equals("toString"))return "SailDroid private storage";if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return proxy==a[0];
        if(n.equals("getVolumeList"))return new StorageVolume[]{volume()};
        if(n.equals("getVolumes")){VolumeInfo info=new VolumeInfo("saildroid:private",VolumeInfo.TYPE_EMULATED,null,null);info.path=storage().getPath();info.internalPath=info.path;info.state=VolumeInfo.STATE_MOUNTED;info.mountFlags=VolumeInfo.MOUNT_FLAG_PRIMARY|VolumeInfo.MOUNT_FLAG_VISIBLE;info.mountUserId=Process.myUserHandle().getIdentifier();return new VolumeInfo[]{info};}
        if(n.equals("getDisks"))return new DiskInfo[0];
        if(n.equals("registerListener")){listeners.add(((IStorageEventListener)a[0]).asBinder());return null;}
        if(n.equals("unregisterListener")){listeners.remove(((IStorageEventListener)a[0]).asBinder());return null;}
        if(n.equals("mkdirs")){
            if(!SdApkPackage.NAME.equals(a[0]))throw new SecurityException("Storage package mismatch");File directory=new File((String)a[1]);String base=storage().getCanonicalPath()+"/Android/";
            if(!directory.getCanonicalPath().startsWith(base))throw new SecurityException("Outside private app storage");if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("Cannot create app storage directory");return null;
        }
        if(n.equals("isUserKeyUnlocked"))return (Integer)a[0]==Process.myUserHandle().getIdentifier();
        throw new UnsupportedOperationException("Private storage: "+method.toGenericString());
    }
}
