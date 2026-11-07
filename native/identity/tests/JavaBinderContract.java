import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.os.Process;
import com.android.internal.os.BinderInternal;
import java.io.File;
import java.nio.file.Files;

/** VM-only transport contract using real matching Android Java/Parcel/JNI Binder. */
public final class JavaBinderContract {
    private static final String SERVICE="org.saildroid.internal.BinderIdentityContract";
    private static final String CALLBACK="org.saildroid.internal.BinderIdentityCallback";
    private static void check(boolean condition,String reason) {
        if(!condition)throw new AssertionError(reason);
    }
    public static void main(String[] args)throws Exception {
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);
        System.load(System.getProperty("saidroid.bridge.library"));
        String root=System.getProperty("saidroid.native.root");
        String dirs=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"
                +root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        check(SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",dirs),"Native runtime load");
        check(SdBridge.configurePrivateBinder(args[1]),"Actual private Binder configure");
        check(SdBridge.registerFrameworkNatives()==100,"Matching JNI registrations");
        SdBridge.startBinderPool();
        final int own=Integer.parseInt(args[2]),peer=Integer.parseInt(args[3]);
        check(Process.myUid()==own&&android.system.Os.getuid()==own,"Actual kernel UID");
        if(args[0].equals("server")) {
            Binder service=new Binder() {
                @Override protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)
                        throws android.os.RemoteException {
                    if(code==IBinder.INTERFACE_TRANSACTION){reply.writeString(SERVICE);return true;}
                    if(code!=42)return super.onTransact(code,data,reply,flags);
                    data.enforceInterface(SERVICE);
                    int forgedUid=data.readInt(),value=data.readInt();
                    IBinder callback=data.readStrongBinder();
                    int callerUid=Binder.getCallingUid(),callerPid=Binder.getCallingPid();
                    check(forgedUid==0&&callerUid==peer&&callerUid!=own,"Kernel caller identity, ignore payload UID");
                    check(Binder.isHandlingTransaction()&&callerPid!=Process.myPid(),"Actual remote transaction");
                    long identity=Binder.clearCallingIdentity();
                    check(Binder.getCallingUid()==own,"Clear identity enters actual service UID");
                    Binder.restoreCallingIdentity(identity);
                    check(Binder.getCallingUid()==peer,"Restore actual caller identity");
                    check(callback!=null&&callback.queryLocalInterface(CALLBACK)==null,"Remote callback object");
                    Parcel request=Parcel.obtain(),answer=Parcel.obtain();
                    int transformed;
                    try {
                        request.writeInterfaceToken(CALLBACK);request.writeInt(value);
                        check(callback.transact(66,request,answer,0),"Actual callback transact");
                        answer.readException();transformed=answer.readInt();
                        check(answer.readInt()==own,"Callback saw service's kernel UID");
                    } finally {request.recycle();answer.recycle();}
                    check(transformed==43,"Real callback payload round trip");
                    reply.writeNoException();reply.writeInt(transformed+1);
                    reply.writeInt(callerUid);reply.writeInt(callerPid);
                    System.out.println("JAVA_BINDER_SERVICE=handled|uid="+own+"|kernel_caller="+callerUid+"|forged_uid_ignored=true|callback=true|identity_clear_restore=true");
                    return true;
                }
            };
            check(SdBridge.becomeBinderContextManager(service),"Own private context manager");
            File ready=new File(args[4]);Files.write(ready.toPath(),("uid="+own+"\n").getBytes("UTF-8"));
            long deadline=System.nanoTime()+25_000_000_000L;
            File stop=new File(args[5]);
            while(!stop.exists()&&System.nanoTime()<deadline)Thread.sleep(30);
            check(stop.exists(),"Supervisor completed actual client before bounded shutdown");
            System.out.println("JAVA_BINDER_SERVER=ready|uid="+own+"|transport=matching-android-jni-kernel");
        } else {
            check(args[0].equals("client"),"Explicit test role");
            IBinder context=BinderInternal.getContextObject();
            check(context!=null&&context.queryLocalInterface(SERVICE)==null,"Remote real context object");
            Binder callback=new Binder() {
                @Override protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)
                        throws android.os.RemoteException {
                    if(code!=66)return super.onTransact(code,data,reply,flags);
                    data.enforceInterface(CALLBACK);int value=data.readInt();
                    check(Binder.getCallingUid()==peer&&Binder.isHandlingTransaction(),"Callback kernel identity");
                    check(Binder.getCallingPid()!=Process.myPid(),"Callback remote process");
                    reply.writeNoException();reply.writeInt(value+1);reply.writeInt(Binder.getCallingUid());
                    System.out.println("JAVA_BINDER_CALLBACK=handled|uid="+own+"|kernel_caller="+Binder.getCallingUid());
                    return true;
                }
            };
            Parcel request=Parcel.obtain(),answer=Parcel.obtain();
            try {
                request.writeInterfaceToken(SERVICE);request.writeInt(0);request.writeInt(42);
                request.writeStrongBinder(callback);
                check(context.transact(42,request,answer,0),"Actual context transaction");
                answer.readException();check(answer.readInt()==44,"Actual nested Binder result");
                check(answer.readInt()==own&&answer.readInt()==Process.myPid(),"Service saw actual kernel credentials");
            } finally {request.recycle();answer.recycle();}
            check(Binder.getCallingUid()==own&&!Binder.isHandlingTransaction(),"Outside-transaction identity");
            System.out.println("JAVA_BINDER_CLIENT=ready|uid="+own+"|remote_uid="+peer+"|payload=42,43,44|callback=true|kernel_identity=true");
        }
        System.out.flush();System.err.flush();System.exit(0);
    }
}
