import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.IBinder;
import java.util.*;

/** Hosted permission prompt; only supported, requested permissions can be granted. */
public final class SdPermissionController {
    public static final String PACKAGE="org.saildroid.permissioncontroller";
    private static final HashSet<IBinder> pending=new HashSet<IBinder>();
    public static boolean accepts(Intent intent){return PackageManager.ACTION_REQUEST_PERMISSIONS.equals(intent.getAction())&&PACKAGE.equals(intent.getPackage())&&intent.getComponent()==null;}
    public static void request(final Activity activity,final IBinder token,Intent intent,final String who,final int code){
        if(!accepts(intent)||!pending.add(token))throw new IllegalStateException("Invalid or overlapping permission request");
        final String[] names=intent.getStringArrayExtra(PackageManager.EXTRA_REQUEST_PERMISSIONS_NAMES);
        if(names==null||names.length>64){pending.remove(token);throw new IllegalArgumentException("Invalid requested permission array");}
        try{
            final SdAppPermissions state=new SdAppPermissions(SdApkPackage.APK,SdApkPackage.NAME);
            boolean any=false;for(String name:names){if(name==null)throw new IllegalArgumentException("Null permission name");any|=state.supported(name)&&!state.holds(name);}
            final boolean[] completed={false};
            final java.util.function.Consumer<Boolean> finish=grant->{
                if(completed[0])return;completed[0]=true;pending.remove(token);int[] results=new int[names.length];
                for(int i=0;i<names.length;i++){
                    if(!state.holds(names[i])&&state.supported(names[i]))state.decide(names[i],grant);
                    results[i]=state.holds(names[i])?PackageManager.PERMISSION_GRANTED:PackageManager.PERMISSION_DENIED;
                    System.err.println("SDPERMISSION=result|permission="+names[i]+"|granted="+(results[i]==PackageManager.PERMISSION_GRANTED)+"|request_code="+code);
                }
                Intent result=new Intent().putExtra(PackageManager.EXTRA_REQUEST_PERMISSIONS_NAMES,names).putExtra(PackageManager.EXTRA_REQUEST_PERMISSIONS_RESULTS,results);
                ArrayList<ResultInfo> values=new ArrayList<ResultInfo>();values.add(new ResultInfo(who,code,Activity.RESULT_OK,result));
                ActivityThread.currentActivityThread().handleSendResult(token,values,"SailDroid runtime permission decision");
                System.err.println("SDPERMISSION=callback_delivered|request_code="+code+"|count="+names.length);
            };
            if(!any){finish.accept(false);return;}
            CharSequence label=activity.getApplicationInfo().loadLabel(activity.getPackageManager());
            boolean camera=Arrays.asList(names).contains("android.permission.CAMERA")&&state.supported("android.permission.CAMERA");
            boolean storage=Arrays.asList(names).contains("android.permission.READ_EXTERNAL_STORAGE")||Arrays.asList(names).contains("android.permission.WRITE_EXTERNAL_STORAGE");
            String access=camera?(storage?"摄像头、照片和共享文件":"摄像头"):"照片和共享文件";
            AlertDialog dialog=new AlertDialog.Builder(activity).setTitle("允许“"+label+"”访问"+access+"？")
                    .setMessage(camera?"允许后，此应用可使用手机真实摄像头。麦克风权限尚不受支持。":Arrays.asList(names).contains("android.permission.WRITE_EXTERNAL_STORAGE")?"允许后，可在应用中浏览手机照片和读写 SailDroid 共享文件。":"允许后，可在应用中浏览手机照片和共享文件。")
                    .setPositiveButton("允许",(d,which)->finish.accept(true))
                    .setNegativeButton("不允许",(d,which)->finish.accept(false))
                    .setOnCancelListener(d->finish.accept(false)).create();
            dialog.show();
            if(System.getenv("SAILDROID_DIAG_INPUT")!=null)dialog.getWindow().getDecorView().post(()->{
                for(int which:new int[]{DialogInterface.BUTTON_POSITIVE,DialogInterface.BUTTON_NEGATIVE}){
                    android.widget.Button button=dialog.getButton(which);int[] point=new int[2];button.getLocationOnScreen(point);
                    System.err.println("SDPERMISSION=button_geometry|request_code="+code+"|choice="+(which==DialogInterface.BUTTON_POSITIVE?"allow":"deny")+"|x="+(point[0]+button.getWidth()/2)+"|y="+(point[1]+button.getHeight()/2));
                }
            });
            System.err.println("SDPERMISSION=prompt_shown|request_code="+code+"|count="+names.length);
        }catch(Exception failure){pending.remove(token);throw new IllegalStateException("Permission request failed",failure);}
    }
}
