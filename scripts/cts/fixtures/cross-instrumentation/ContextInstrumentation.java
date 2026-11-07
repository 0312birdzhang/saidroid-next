package org.example.saildroid.instrumentrunner;
import android.app.Instrumentation;
import android.app.Activity;
import android.os.Bundle;
import android.content.Context;
import java.io.*;

public final class ContextInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle arguments){super.onCreate(arguments);start();}
    @Override public void onStart(){
        Bundle output=new Bundle();
        try{
            Context runner=getContext(),target=getTargetContext();
            if(!"org.example.saildroid.instrumentrunner".equals(runner.getPackageName())||!"org.example.saildroid.instrumenttarget".equals(target.getPackageName()))throw new AssertionError("Context packages differ from real manifests");
            String a=read(runner,"proof.txt"),b=read(target,"proof.txt");
            if(!"runner-resource".equals(a)||!"target-resource".equals(b))throw new AssertionError("APK resources were not distinct");
            android.content.pm.PackageManager packages=runner.getPackageManager();
            if(packages.checkPermission("android.permission.INTERNET",runner.getPackageName())!=android.content.pm.PackageManager.PERMISSION_GRANTED||packages.checkPermission("android.permission.INTERNET",target.getPackageName())!=android.content.pm.PackageManager.PERMISSION_DENIED||packages.checkPermission("android.permission.VIBRATE",runner.getPackageName())!=android.content.pm.PackageManager.PERMISSION_DENIED||packages.checkPermission("android.permission.VIBRATE",target.getPackageName())!=android.content.pm.PackageManager.PERMISSION_GRANTED)throw new AssertionError("Named package permissions did not follow each APK manifest");
            if(packages.isInstantApp(runner.getPackageName())||packages.isInstantApp(target.getPackageName())||runner.getApplicationInfo().isInstantApp()||target.getApplicationInfo().isInstantApp())throw new AssertionError("Full APK installation reported as instant");
            File rd=runner.getFilesDir(),td=target.getFilesDir();
            Class<?> dexLoader=Class.forName("dalvik.system.BaseDexClassLoader");
            java.lang.reflect.Constructor<?> constructor=dexLoader.getConstructor(String.class,File.class,String.class,ClassLoader.class,boolean.class);
            constructor.newInstance(runner.getApplicationInfo().sourceDir,rd,null,target.getClassLoader(),false);
            boolean trustDenied=false;
            try{constructor.newInstance(runner.getApplicationInfo().sourceDir,rd,null,target.getClassLoader(),true);}catch(java.lang.reflect.InvocationTargetException denied){if(denied.getCause()instanceof SecurityException)trustDenied=true;else throw denied;}
            if(!trustDenied)throw new AssertionError("Unsupported DEX trust elevation was accepted");
            target.getClassLoader().loadClass("android.test.AndroidTestCase");
            try(InputStream input=target.getContentResolver().openInputStream(android.net.Uri.parse("content://android.tradefed.contentprovider/sdcard/dynamic-config-files/proof.dynamic"))){byte[] bytes=new byte[64];int count=input.read(bytes);if(!"actual-config-file".equals(new String(bytes,0,count,"UTF-8")))throw new AssertionError("Prepared configuration bytes differ");}
            boolean writeDenied=false;
            try{target.getContentResolver().openFileDescriptor(android.net.Uri.parse("content://android.tradefed.contentprovider/sdcard/dynamic-config-files/proof.dynamic"),"w");}catch(FileNotFoundException denied){writeDenied=true;}
            if(!writeDenied)throw new AssertionError("Prepared configuration was writable");
            if(rd.getCanonicalPath().equals(td.getCanonicalPath())||!rd.getCanonicalPath().startsWith("/home/art/apps/org.example.saildroid.instrumentrunner/data/")||!td.getCanonicalPath().startsWith("/home/art/apps/org.example.saildroid.instrumenttarget/data/"))throw new AssertionError("Private data roots differ from real installations");
            Class<?> cls=runner.getClassLoader().loadClass("org.example.saildroid.instrumenttarget.TargetState");
            if(cls!=target.getClassLoader().loadClass(cls.getName())||cls.getField("starts").getInt(null)!=1)throw new AssertionError("Target class loader identity differs");
            if(target.getClassLoader().loadClass(ContextInstrumentation.class.getName())!=ContextInstrumentation.class||runner.getClassLoader().loadClass(ContextInstrumentation.class.getName())!=ContextInstrumentation.class)throw new AssertionError("Target loader cannot discover the actual test APK class with shared identity");
            File rf=new File(rd,"runner-only.txt"),tf=new File(td,"target-only.txt");
            try(FileOutputStream file=new FileOutputStream(rf)){file.write(1);}
            try(FileOutputStream file=new FileOutputStream(tf)){file.write(2);}
            if(!rf.isFile()||!tf.isFile()||new File(rd,"target-only.txt").exists()||new File(td,"runner-only.txt").exists())throw new AssertionError("Context data isolation failed");
            for(final boolean mode:new boolean[]{false,true}){
                setInTouchMode(mode);
                final android.app.Activity page=startActivitySync(new android.content.Intent().setClassName(target.getPackageName(),"org.example.saildroid.instrumenttarget.ModeActivity").addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK));
                waitForIdleSync();
                final boolean[] matched={false};
                long deadline=android.os.SystemClock.uptimeMillis()+3000;
                do{
                    runOnMainSync(new Runnable(){public void run(){android.view.View view=page.getWindow().getDecorView();matched[0]=view.isAttachedToWindow()&&view.isInTouchMode()==mode;}});
                    if(matched[0])break;
                    android.os.SystemClock.sleep(20);
                }while(android.os.SystemClock.uptimeMillis()<deadline);
                runOnMainSync(new Runnable(){public void run(){page.finish();}});
                waitForIdleSync();
                if(!matched[0])throw new AssertionError("Actual ViewRoot touch mode did not match Instrumentation request: "+mode);
            }
            output.putString("class","ContextInstrumentation");output.putString("test","separate-manifests-resources-data-and-loader");sendStatus(1,output);sendStatus(0,output);
            output.putString("stream","CROSS_INSTRUMENTATION=PASS|resources=distinct|private_roots=distinct|target_loader=shared|permissions=own-manifest|viewroot_touch_modes=false,true|last_activity_keeps_instrumentation=true|full_apk_installation=true\n");finish(Activity.RESULT_OK,output);
        }catch(Throwable error){output.putString("stream",error.toString());finish(Activity.RESULT_CANCELED,output);}
    }
    private String read(Context ctx,String name)throws Exception{try(InputStream input=ctx.getAssets().open(name)){byte[] bytes=new byte[128];int count=input.read(bytes);return new String(bytes,0,count,"UTF-8");}}
}
