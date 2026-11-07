package org.example.saildroid.identitylaunch;
import android.app.Instrumentation;
import android.os.Bundle;
import android.os.Process;
import android.system.Os;
import android.content.pm.PackageManager;
import java.io.File;
import java.nio.file.Files;

/** Internal true APK/framework/kernel identity contract, not a CTS test. */
public final class IdentityLaunchInstrumentation extends Instrumentation {
    private Bundle arguments;
    @Override public void onCreate(Bundle args) { arguments = args; start(); }
    private static void check(boolean value, String reason) { if (!value) throw new AssertionError(reason); }
    private static byte[] read(java.io.InputStream input) throws java.io.IOException {
        try(java.io.ByteArrayOutputStream output=new java.io.ByteArrayOutputStream()) {
            byte[] block=new byte[4096];int count;
            while((count=input.read(block))!=-1)output.write(block,0,count);
            return output.toByteArray();
        }
    }
    @Override public void onStart() {
        Bundle status = new Bundle();
        String test = "actualApkIdentityAndPrivateData";
        status.putString("class",getClass().getName());status.putString("test",test);
        status.putInt("numtests",1);status.putInt("current",1);sendStatus(1,status);
        Bundle result = new Bundle();
        try {
            int uid = Integer.parseInt(arguments.getString("expected_uid"));
            check(uid >= 10000 && uid <= 19999 && Process.myUid()==uid && Os.getuid()==uid,
                    "APK process does not use actual assigned kernel identity");
            check(getTargetContext().getApplicationInfo().uid==uid,
                    "Actual application metadata UID differs");
            check(getTargetContext().getPackageName().equals("org.example.saildroid.identitylaunch"),
                    "Wrong actual bound APK target context");
            check(getContext().getPackageName().equals(getTargetContext().getPackageName()),
                    "Instrumentation context differs from declared package");
            check(getTargetContext().getApplicationInfo().targetSdkVersion==29,
                    "Actual declared APK target SDK differs");
            File proof=new File(getTargetContext().getFilesDir(),"actual-apk-uid.txt");
            Files.write(proof.toPath(),("uid="+uid+"\n").getBytes("UTF-8"));
            check(Os.stat(proof.getPath()).st_uid==uid,"APK file has wrong kernel owner");
            check(new String(Files.readAllBytes(proof.toPath()),"UTF-8").equals("uid="+uid+"\n"),
                    "APK private data round trip differs");
            check(getTargetContext().checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS")
                    ==PackageManager.PERMISSION_DENIED,"Signature permission invented for APK");
            String key="ro.debuggable";
            java.lang.Process command = new ProcessBuilder("getprop", key).start();
            String cli=new String(read(command.getInputStream()),"UTF-8").trim();
            check(command.waitFor()==0,"Private getprop process failed");
            String actual = android.os.SystemProperties.get(key);
            check(cli.equals(actual),"Actual Java/native property and command backend differ");
            java.lang.Process sdkCommand = new ProcessBuilder("getprop", "ro.build.version.sdk").start();
            String sdk=new String(read(sdkCommand.getInputStream()),"UTF-8").trim();
            check(sdkCommand.waitFor()==0&&sdk.equals(String.valueOf(android.os.Build.VERSION.SDK_INT)),
                    "Actual framework SDK and command property differ");
            java.lang.Process missing = new ProcessBuilder("getprop", "saildroid.private.unknown", "fallback-proof").start();
            check(new String(read(missing.getInputStream()),"UTF-8").equals("fallback-proof\n")&&missing.waitFor()==0,
                    "Unknown native property fallback differs");
            System.out.println("PRIVATE_GETPROP_PARITY=ready|java_ro_debuggable="+actual+"|command_ro_debuggable="+cli+"|actual_sdk="+sdk+"|host_property_reader=false");
            String process=new String(Files.readAllBytes(new File("/proc/self/status").toPath()),"UTF-8");
            check(process.contains("NoNewPrivs:\t1"),"NoNewPrivs missing in actual APK process");
            status.putString("stream",". actual kernel UID="+uid+" private app data and signature permission boundary\n");
            sendStatus(0,status);result.putString("stream","OK (1 test)\n");
            System.out.println("IDENTITY_APK_LAUNCH=ready|kernel_uid="+uid+"|context_uid="+
                    getTargetContext().getApplicationInfo().uid+"|target_sdk=29|actual_private_file_owner=true|signature_permission=denied");
        } catch(Throwable error) {
            status.putString("stack",android.util.Log.getStackTraceString(error));
            sendStatus(-2,status);result.putString("stream","FAILURES!!!\nTests run: 1, Failures: 1\n");
        }
        finish(android.app.Activity.RESULT_OK,result);
    }
}
