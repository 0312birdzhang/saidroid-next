import android.os.Binder;
import android.os.Process;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.ByteArrayOutputStream;
import java.util.Iterator;
import org.json.JSONObject;

/** A root-sealed decision snapshot, consumed using actual kernel Binder callers.
 * The trusted supervisor genuinely verifies APKs and compiles their facts with
 * ServiceAccess before publishing this file. No caller-supplied UID is accepted.
 */
public final class VerifiedServicePolicy {
    private final JSONObject callers,services;
    private static void require(boolean value,String reason){if(!value)throw new SecurityException(reason);}
    private static int uid(Object value){
        require(value instanceof Integer,"Policy UID must be an actual integer");
        int uid=(Integer)value;require(uid>=10000&&uid<=19999,"Policy UID outside app range");return uid;
    }
    public VerifiedServicePolicy(File source)throws Exception {
        require(source.isAbsolute()&&source.getCanonicalFile().equals(source),"Canonical immutable policy required");
        for(File parent=source.getParentFile();parent!=null;parent=parent.getParentFile()){
            StructStat s=Os.lstat(parent.getPath());
            require(OsConstants.S_ISDIR(s.st_mode)&&s.st_uid==0&&(s.st_mode&0022)==0,"Untrusted policy ancestor");
        }
        FileDescriptor descriptor=Os.open(source.getPath(),OsConstants.O_RDONLY|OsConstants.O_CLOEXEC|OsConstants.O_NOFOLLOW,0);
        JSONObject json;
        try(FileInputStream input=new FileInputStream(descriptor)){
            StructStat before=Os.fstat(descriptor);
            require(OsConstants.S_ISREG(before.st_mode)&&before.st_uid==0&&before.st_nlink==1&&
                    (before.st_mode&0777)==0444&&before.st_size>0&&before.st_size<=4*1024*1024,"Unsealed service policy");
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] block=new byte[4096];int count;
            while((count=input.read(block))!=-1){bytes.write(block,0,count);require(bytes.size()<=4*1024*1024,"Oversized policy");}
            StructStat after=Os.fstat(descriptor);
            require(before.st_dev==after.st_dev&&before.st_ino==after.st_ino&&before.st_size==after.st_size&&
                    before.st_mtime==after.st_mtime&&bytes.size()==before.st_size,"Policy changed while reading");
            json=new JSONObject(new String(bytes.toByteArray(),"UTF-8"));
        }
        require(json.length()==4&&"saildroid-verified-service-policy-v1".equals(json.get("schema")),"Policy schema differs");
        callers=json.getJSONObject("callers");services=json.getJSONObject("services");JSONObject apks=json.getJSONObject("apk_hashes");
        require(callers.length()>0&&callers.length()<=10000&&apks.length()==callers.length(),"Invalid caller snapshot");
        Iterator<String> keys=callers.keys();
        while(keys.hasNext()){
            String key=keys.next();int actual=Integer.parseInt(key);require(String.valueOf(actual).equals(key),"Noncanonical policy UID");uid(Integer.valueOf(actual));
            String name=callers.getString(key);require(name.matches("[A-Za-z][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)+"),"Invalid policy package");
            require(apks.getString(name).matches("[a-f0-9]{64}"),"Missing actual APK hash");
        }
        keys=services.keys();
        while(keys.hasNext()){
            String component=keys.next();JSONObject service=services.getJSONObject(component);
            require(component.matches("[A-Za-z][A-Za-z0-9_.]*/[A-Za-z_$][A-Za-z0-9_.$]*")&&service.length()==3,"Invalid service declaration");
            int owner=uid(service.get("owner_uid"));
            require(component.startsWith(callers.getString(String.valueOf(owner))+"/")&&service.get("registration_enabled")instanceof Boolean,"Service owner/declaration differs");
            JSONObject rules=service.getJSONObject("callers");require(rules.length()==callers.length(),"Policy caller set differs");
            Iterator<String> users=rules.keys();
            while(users.hasNext()){
                String user=users.next();require(callers.has(user),"Unknown policy caller");
                Object decision=rules.get(user);require(decision instanceof String&&((String)decision).matches("(allow:(own-uid|exported|normal-requested|verified-signature)|deny:(disabled|not-exported|permission-not-requested|unknown-permission|permission-backend-unavailable|signature-mismatch))"),"Unknown service decision");
            }
        }
    }
    public String enforceCaller(String component)throws Exception {
        require(Binder.isHandlingTransaction(),"A real Binder transaction is required");
        int caller=Binder.getCallingUid();
        require(callers.has(String.valueOf(caller)),"deny:unknown-kernel-uid");
        require(services.has(component),"deny:undeclared-service");
        String decision=services.getJSONObject(component).getJSONObject("callers").getString(String.valueOf(caller));
        require(decision.startsWith("allow:"),decision);return decision;
    }
    public String enforceRegistration(String component)throws Exception {
        int caller=Binder.isHandlingTransaction()?Binder.getCallingUid():Process.myUid();
        require(services.has(component),"deny:undeclared-service");JSONObject service=services.getJSONObject(component);
        require(uid(service.get("owner_uid"))==caller,"deny:not-owner");
        require(service.getBoolean("registration_enabled"),"deny:disabled");return "allow:declared-owner";
    }
}
