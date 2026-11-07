import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.os.Process;
import com.android.internal.os.BinderInternal;
import java.io.File;
import java.nio.file.Files;

/** Actual Java Binder authorization using root-verified APK facts. No Service
 * class execution or original CTS acceptance is claimed by this internal test. */
public final class JavaVerifiedServiceContract {
    private static final String DESCRIPTOR="org.saildroid.internal.VerifiedServiceContract";
    private static void check(boolean value,String reason){if(!value)throw new AssertionError(reason);}
    public static void main(String[] args)throws Exception {
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);
        System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root");
        String dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Native load");
        check(SdBridge.configurePrivateBinder(args[1]),"Actual private Binder driver");
        check(SdBridge.registerFrameworkNatives()==100,"Matching JNI100");SdBridge.startBinderPool();
        int own=Integer.parseInt(args[2]);check(Process.myUid()==own&&android.system.Os.getuid()==own,"Actual kernel UID");
        if(args[0].equals("server")) {
            final VerifiedServicePolicy policy=new VerifiedServicePolicy(new File(args[3]));
            policy.enforceRegistration(args[4]);
            Binder service=new Binder(){
                @Override protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)
                        throws android.os.RemoteException {
                    if(code!=42&&code!=43)return super.onTransact(code,data,reply,flags);
                    data.enforceInterface(DESCRIPTOR);String component=data.readString();
                    int forged=data.readInt(),value=data.readInt();int caller=Binder.getCallingUid();
                    check(forged==0&&value==42&&Binder.isHandlingTransaction()&&Binder.getCallingPid()!=Process.myPid(),"Real Binder request and credentials");
                    String decision;
                    try {decision=code==42?policy.enforceCaller(component):policy.enforceRegistration(component);}
                    catch(SecurityException denied){
                        reply.writeException(denied);
                        System.out.println("JAVA_VERIFIED_SERVICE=handled|kernel_uid="+caller+"|operation="+code+"|component="+component+"|decision="+denied.getMessage()+"|claimed_uid_ignored=true");
                        return true;
                    } catch(Exception failure){throw new android.os.RemoteException("Real service policy backend failed: "+failure);}
                    reply.writeNoException();reply.writeString(decision);reply.writeInt(caller);reply.writeInt(Process.myUid());reply.writeInt(value+1);
                    System.out.println("JAVA_VERIFIED_SERVICE=handled|kernel_uid="+caller+"|operation="+code+"|component="+component+"|decision="+decision+"|claimed_uid_ignored=true");
                    return true;
                }
            };
            check(SdBridge.becomeBinderContextManager(service),"Own actual context manager");
            Files.write(new File(args[5]).toPath(),("uid="+own+"\n").getBytes("UTF-8"));
            File stop=new File(args[6]);long deadline=System.nanoTime()+50_000_000_000L;
            while(!stop.exists()&&System.nanoTime()<deadline)Thread.sleep(30);
            check(stop.exists(),"All actual clients completed before shutdown");
            System.out.println("JAVA_VERIFIED_SERVICE_SERVER=ready|uid="+own+"|immutable_verified_policy=true");
        } else {
            check(args[0].equals("client"),"Explicit contract role");
            IBinder remote=BinderInternal.getContextObject();check(remote!=null&&remote.queryLocalInterface(DESCRIPTOR)==null,"Remote kernel Binder object");
            String component=args[3],expected=args[5];int operation=Integer.parseInt(args[4]);boolean allowed=expected.startsWith("allow:");
            Parcel request=Parcel.obtain(),answer=Parcel.obtain();
            try {
                request.writeInterfaceToken(DESCRIPTOR);request.writeString(component);request.writeInt(0);request.writeInt(42);
                check(remote.transact(operation,request,answer,0),"Actual remote policy transaction");
                try {
                    answer.readException();check(allowed,"Unauthorized real Binder call was permitted");
                    check(answer.readString().equals(expected)&&answer.readInt()==own&&answer.readInt()==Integer.parseInt(args[6])&&answer.readInt()==43,"Actual permission decision, credentials and payload");
                } catch(SecurityException denied){check(!allowed&&denied.getMessage().contains(expected),"Actual denial differs: "+denied);}
            }finally{request.recycle();answer.recycle();}
            System.out.println("JAVA_VERIFIED_SERVICE_CLIENT=ready|actual_uid="+own+"|component="+component+"|operation="+operation+"|decision="+expected+"|kernel_binder=true");
        }
        System.out.flush();System.err.flush();System.exit(0);
    }
}
