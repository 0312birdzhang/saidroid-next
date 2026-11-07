package org.saildroid.manager;

import android.content.Intent;
import android.content.pm.PackageParser;
import android.content.pm.Signature;
import android.content.res.AssetManager;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.util.Base64;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.nio.channels.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

/** Signed APK installation and reversible updates in the ordinary user's store. */
public final class SdAppRegistry {
    public interface Progress { void update(String message); }
    private static final File APPS=new File(System.getProperty("saidroid.apps.directory","/home/art/apps"));
    private static final File DESKTOP=new File(System.getProperty("saidroid.desktop.directory",new File(System.getenv("HOME"),".local/share/applications").getAbsolutePath()));
    public static boolean validName(String name){return name!=null&&name.matches("[A-Za-z][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)+")&&!name.equals("android")&&!name.startsWith("org.saildroid.");}
    private static void directory(File file)throws IOException{if(!file.isDirectory()&&!file.mkdirs())throw new IOException("无法创建应用目录");}
    private static File child(File parent,String name)throws IOException{File file=new File(parent,name);if(!new File(parent.getCanonicalFile(),name).getAbsolutePath().equals(file.getCanonicalPath()))throw new IOException("应用目录包含无效链接");return file;}
    private static File app(String name)throws IOException{if(!validName(name))throw new IllegalArgumentException("无效的软件包名称");return child(APPS,name);}
    private static byte[] bytes(File file)throws IOException{try(InputStream in=new FileInputStream(file);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] data=new byte[65536];int n;while((n=in.read(data))>0)out.write(data,0,n);return out.toByteArray();}}
    private static JSONObject read(File file)throws Exception{return new JSONObject(new String(bytes(file),"UTF-8"));}
    private static void atomic(File file,byte[] value)throws IOException{atomic(file,value,false);}
    private static void atomic(File file,byte[] value,boolean executable)throws IOException{
        directory(file.getParentFile());File temp=File.createTempFile(".saidroid-",".tmp",file.getParentFile());boolean saved=false;
        try{try(FileOutputStream out=new FileOutputStream(temp)){out.write(value);out.getFD().sync();}temp.setReadable(true,false);if(executable&&!temp.setExecutable(true,false))throw new IOException("无法启用应用启动入口");if(!temp.renameTo(file))throw new IOException("无法保存安装记录");saved=true;}finally{if(!saved)temp.delete();}
    }
    private static void write(File file,JSONObject value)throws Exception{atomic(file,value.toString(2).getBytes("UTF-8"));}
    private static String hex(byte[] bytes){StringBuilder out=new StringBuilder();for(byte value:bytes)out.append(String.format(Locale.US,"%02x",value&255));return out.toString();}
    private static String sha(File file)throws Exception{MessageDigest digest=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){byte[] block=new byte[65536];int n;while((n=in.read(block))>0)digest.update(block,0,n);}return hex(digest.digest());}
    private static void copy(InputStream in,File target)throws IOException{try(OutputStream out=new FileOutputStream(target)){byte[] block=new byte[65536];int n;while((n=in.read(block))>0)out.write(block,0,n);}}
    private static List<String> signers(Signature[] signatures)throws Exception{ArrayList<String> result=new ArrayList<String>();if(signatures!=null)for(Signature signature:signatures)result.add(hex(MessageDigest.getInstance("SHA-256").digest(signature.toByteArray())));Collections.sort(result);return result;}
    public static JSONObject get(String name)throws Exception{JSONObject value=read(child(app(name),"record.json"));if(!name.equals(value.getString("package")))throw new IOException("安装记录不匹配");return value;}
    public static List<JSONObject> installed(){ArrayList<JSONObject> result=new ArrayList<JSONObject>();File[] dirs=APPS.listFiles();if(dirs!=null)for(File dir:dirs)if(validName(dir.getName()))try{result.add(get(dir.getName()));}catch(Exception ignored){System.err.println("APP_REGISTRY=invalid_record|package="+dir.getName());}return result;}
    private static final class StopLock implements Closeable {
        final RandomAccessFile file;final FileLock lock;
        StopLock(String name)throws IOException{try{if(new JSONObject(NativeHost.state(name)).optBoolean("running"))throw new IOException("请先关闭应用，再更新或卸载。");}catch(IOException failure){throw failure;}catch(Exception failure){throw new IOException("应用状态不可用",failure);}File runtime=new File(System.getProperty("saidroid.runtime.directory","/run/user/"+android.os.Process.myUid()+"/saildroid"));directory(runtime);file=new RandomAccessFile(new File(runtime,name+".lock"),"rw");FileLock held;
            try{held=file.getChannel().tryLock();}catch(OverlappingFileLockException busy){held=null;}
            if(held==null){file.close();throw new IOException("请先关闭应用，再更新或卸载。");}lock=held;}
        public void close()throws IOException{lock.release();file.close();}
    }
    public static synchronized JSONObject install(File source,Progress progress)throws Exception{
        if(!source.isFile()||source.length()==0)throw new IOException("找不到 APK 文件");directory(APPS);
        File stage=child(APPS,".install-"+android.os.Process.myPid()+"-"+System.nanoTime());if(!stage.mkdir())throw new IOException("无法创建安装目录");
        try{
            progress.update("正在读取安装包…");File apk=new File(stage,"base.apk");try(InputStream in=new FileInputStream(source)){copy(in,apk);}
            PackageParser parser=new PackageParser();PackageParser.Package metadata=parser.parsePackage(apk,0);
            if(!validName(metadata.packageName))throw new SecurityException("此软件包名称不能安装");
            progress.update("正在验证安装包签名…");PackageParser.collectCertificates(metadata,false);
            Signature[] signatures=metadata.mSigningDetails.signatures;List<String> identities=signers(signatures);if(identities.isEmpty())throw new SecurityException("安装包没有有效签名");
            try(StopLock stopped=new StopLock(metadata.packageName)){
                File app=app(metadata.packageName),recordFile=child(app,"record.json");byte[] previous=recordFile.isFile()?bytes(recordFile):null;
                if(previous!=null){JSONArray saved=new JSONObject(new String(previous,"UTF-8")).getJSONArray("signers");ArrayList<String> old=new ArrayList<String>();for(int i=0;i<saved.length();i++)old.add(saved.getString(i));Collections.sort(old);if(!old.equals(identities))throw new SecurityException("此更新的签名与已安装应用不同");}
                progress.update("正在安装应用组件…");File libraries=new File(stage,"lib");directory(libraries);boolean nativeCode=false,arm64=false;HashSet<String> names=new HashSet<String>();
                try(ZipFile zip=new ZipFile(apk)){Enumeration<? extends ZipEntry> entries=zip.entries();while(entries.hasMoreElements()){
                    ZipEntry entry=entries.nextElement();String name=entry.getName();if(name.startsWith("lib/")&&name.endsWith(".so")&&!entry.isDirectory())nativeCode=true;
                    if(!name.startsWith("lib/arm64-v8a/")||entry.isDirectory())continue;
                    String basename=name.substring(14);if(!basename.matches("[A-Za-z0-9_+.-]+\\.so(?:\\.[0-9]+)*")||basename.contains("..")||basename.contains("_bio.so")||!names.add(basename))throw new SecurityException("安装包包含无效或重复的组件路径");
                    File destination=new File(libraries,basename);try(InputStream in=zip.getInputStream(entry)){copy(in,destination);}
                    // Android extracts signed entries by ABI directory. Some
                    // vendors keep opaque or placeholder payloads named .so;
                    // the loader validates executable ELF when an app loads it.
                    arm64=true;
                }}
                if(nativeCode&&!arm64)throw new IllegalArgumentException("此安装包没有 arm64 组件，请选择 arm64-v8a 或纯 Java 安装包");
                String launcher=null;for(PackageParser.Activity activity:metadata.activities)if(activity.info.enabled)for(PackageParser.ActivityIntentInfo filter:activity.intents)if(filter.hasAction(Intent.ACTION_MAIN)&&filter.hasCategory(Intent.CATEGORY_LAUNCHER)){launcher=activity.info.name;break;}
                String label=metadata.applicationInfo.nonLocalizedLabel==null?metadata.packageName:metadata.applicationInfo.nonLocalizedLabel.toString();
                AssetManager assets=new AssetManager();try{
                    if(assets.addAssetPath(apk.getAbsolutePath())==0)throw new IOException("无法读取应用资源");Resources sys=Resources.getSystem();Resources resources=new Resources(assets,sys.getDisplayMetrics(),sys.getConfiguration());
                    if(metadata.applicationInfo.labelRes!=0)label=resources.getText(metadata.applicationInfo.labelRes).toString();Drawable icon;try{icon=resources.getDrawable(metadata.applicationInfo.icon);}catch(Exception missing){icon=sys.getDrawable(android.R.drawable.sym_def_app_icon);}
                    Bitmap bitmap=Bitmap.createBitmap(128,128,Bitmap.Config.ARGB_8888);icon.setBounds(0,0,128,128);icon.draw(new Canvas(bitmap));try(OutputStream out=new FileOutputStream(new File(stage,"icon.png"))){if(!bitmap.compress(Bitmap.CompressFormat.PNG,100,out))throw new IOException("无法保存应用图标");}bitmap.recycle();
                }finally{assets.close();}
                JSONObject record=new JSONObject();record.put("package",metadata.packageName);record.put("debuggable",(metadata.applicationInfo.flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0);record.put("label",label);record.put("versionName",metadata.mVersionName);record.put("versionCode",metadata.mVersionCode);record.put("apkSha256",sha(apk));record.put("signers",new JSONArray(identities));record.put("launchActivity",launcher==null?JSONObject.NULL:launcher);
                JSONArray certificates=new JSONArray();for(Signature signature:signatures)certificates.put(Base64.encodeToString(signature.toByteArray(),Base64.NO_WRAP));record.put("certificates",certificates);
                directory(app);File versions=child(app,"versions");directory(versions);File destination=child(versions,record.getString("apkSha256")+"-"+Long.toHexString(System.nanoTime()));
                if(destination.exists()||!stage.renameTo(destination))throw new IOException("无法保存安装包");File data=child(app,"data");directory(data);
                record.put("apk",new File(destination,"base.apk").getAbsolutePath());record.put("native",new File(destination,"lib").getAbsolutePath());record.put("icon",new File(destination,"icon.png").getAbsolutePath());record.put("data",data.getAbsolutePath());
                try{write(recordFile,record);writeDesktop(record);}catch(Exception failure){if(previous==null)recordFile.delete();else atomic(recordFile,previous);throw failure;}
                progress.update("安装完成");return record;
            }
        }finally{if(stage.exists())deleteTree(stage);}
    }
    private static String desktopText(String value){return value.replace("\\","\\\\").replace("\n","\\n").replace("\r","\\r");}
    public static String desktopId(String name)throws Exception{
        byte[] hash=java.security.MessageDigest.getInstance("SHA-256").digest(name.getBytes("UTF-8"));StringBuilder key=new StringBuilder("org.saildroid.app.p");for(int i=0;i<10;i++)key.append(String.format(java.util.Locale.US,"%02x",hash[i]&255));return key.toString();
    }
    private static File legacyActivationFile(String name)throws Exception{
        File services=new File(System.getenv("HOME"),".local/share/dbus-1/services");return new File(services,desktopId(name)+".service");
    }
    private static void writeDesktop(JSONObject record)throws Exception{
        directory(DESKTOP);String name=record.getString("package");File desktop=new File(DESKTOP,desktopId(name)+".desktop");File legacy=new File(DESKTOP,"saildroid-"+name+".desktop");if(record.isNull("launchActivity")){if(desktop.exists()&&!desktop.delete())throw new IOException("无法移除无启动入口的图标");if(legacy.exists()&&!legacy.delete())throw new IOException("无法移除旧启动入口");File activation=legacyActivationFile(name);if(activation.exists()&&!activation.delete())throw new IOException("无法移除旧启动入口");return;}
        // Sailfish scores Exec tokens against /proc cmdline. The exact Android
        // process-name token lets its shell select the existing Cover directly.
        String launcher=System.getenv("ANDROID_ROOT")+"/libexec/saildroid-app";
        String service=desktopId(name);File oldActivation=legacyActivationFile(name);if(oldActivation.exists()&&!oldActivation.delete())throw new IOException("无法清理旧启动入口");
        String text="[Desktop Entry]\nType=Application\nName="+desktopText(record.getString("label"))+"\nExec="+launcher+" --package "+name+" --desktop-token "+name+"\nIcon="+record.getString("icon")+"\nStartupNotify=true\nX-Sailfish-ApplicationType=generic\n\n[X-Sailjail]\nSandboxing=Disabled\nOrganizationName=org.saildroid.app\nApplicationName="+service.substring("org.saildroid.app.".length())+"\n";atomic(desktop,text.getBytes("UTF-8"));if(legacy.exists()&&!legacy.delete())throw new IOException("无法移除旧启动入口");
    }
    public static synchronized void refreshLaunchers()throws Exception{for(JSONObject record:installed())writeDesktop(record);}
    public static synchronized void uninstall(String name)throws Exception{get(name);try(StopLock stopped=new StopLock(name)){File entry=new File(DESKTOP,desktopId(name)+".desktop");File legacy=new File(DESKTOP,"saildroid-"+name+".desktop");if(entry.exists()&&!entry.delete())throw new IOException("无法移除启动图标");if(legacy.exists()&&!legacy.delete())throw new IOException("无法移除旧启动入口");File activation=legacyActivationFile(name);if(activation.exists()&&!activation.delete())throw new IOException("无法移除启动入口");deleteTree(app(name));}}
    private static void deleteTree(File file)throws IOException{if(file.isDirectory()&&new File(file.getParentFile().getCanonicalFile(),file.getName()).getAbsolutePath().equals(file.getCanonicalPath())){File[] children=file.listFiles();if(children==null)throw new IOException("无法读取卸载目录");for(File child:children)deleteTree(child);}if(file.exists()&&!file.delete())throw new IOException("无法移除文件 "+file.getName());}
    public static void launch(String name)throws Exception{JSONObject record=get(name);if(record.isNull("launchActivity"))throw new IOException("此应用没有启动入口");NativeHost.open(name);}
}
