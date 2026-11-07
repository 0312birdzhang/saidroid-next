import java.io.File;
/** Internal actual-filesystem policy input contract, no CTS test replacement. */
public final class ServicePolicyInputContract {
    public static void main(String[] args)throws Exception {
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);
        System.load(System.getProperty("saidroid.bridge.library"));String root=System.getProperty("saidroid.native.root");
        String paths=root+"/lib64:"+root+"/apex/com.android.runtime.debug/lib64:"+root+"/apex/com.android.conscrypt/lib64:"+root+"/apex/com.android.resolv/lib64";
        if(!SdBridge.loadBionicLibrary(root+"/lib64/libandroid_runtime.so",paths)||SdBridge.registerFrameworkNatives()!=100)
            throw new AssertionError("Actual native input bootstrap");
        boolean accepted=false;String failure="";
        try {
            VerifiedServicePolicy policy=new VerifiedServicePolicy(new File(args[0]));accepted=true;
            try {policy.enforceCaller("org.example.saildroid.serviceowner/org.example.saildroid.servicefixture.PublicService");throw new AssertionError("Non-Binder call was treated as remote");}
            catch(SecurityException expected){if(!expected.getMessage().contains("A real Binder transaction is required"))throw expected;}
        } catch(SecurityException|org.json.JSONException|android.system.ErrnoException refused) {
            failure=refused.toString();
        }
        if(accepted!=Boolean.parseBoolean(args[1]))throw new AssertionError("Actual policy acceptance differs: "+failure);
        System.out.println("SERVICE_POLICY_INPUT=ready|accepted="+accepted+"|failure="+failure+"|uid="+android.os.Process.myUid());
        System.exit(0);
    }
}
