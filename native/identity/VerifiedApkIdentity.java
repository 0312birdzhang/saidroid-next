import android.content.pm.ApplicationInfo;
import android.content.pm.PackageParser;
import android.content.pm.Signature;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.File;
import java.io.FileInputStream;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import org.json.JSONObject;
import org.json.JSONArray;

/** Trusted platform verifier tool; never loads code from the APK under inspection.
 * The privileged caller supplies an immutable root-staged file. Parsing and
 * signature verification run in an ordinary kernel UID, outside the root caller.
 */
public final class VerifiedApkIdentity {
    private static void require(boolean value, String reason) {
        if (!value) throw new SecurityException(reason);
    }
    private static String hex(byte[] value) {
        StringBuilder text = new StringBuilder();
        for (byte item : value) text.append(String.format(java.util.Locale.US, "%02x", item & 255));
        return text.toString();
    }
    private static String digest(File file) throws Exception {
        MessageDigest value = MessageDigest.getInstance("SHA-256");
        try (FileInputStream input = new FileInputStream(file)) {
            byte[] bytes = new byte[65536]; int count;
            while ((count = input.read(bytes)) != -1) value.update(bytes, 0, count);
        }
        return hex(value.digest());
    }
    private static StructStat staged(File file) throws Exception {
        require(file.isAbsolute() && file.getCanonicalFile().equals(file), "APK path is not canonical");
        StructStat item = Os.lstat(file.getPath());
        require(OsConstants.S_ISREG(item.st_mode) && item.st_uid == 0 && item.st_nlink == 1 &&
                (item.st_mode & 0022) == 0 && item.st_size > 0 && item.st_size <= 1024L*1024*1024,
                "APK must be a single-link root-owned immutable staged file");
        for (File parent = file.getParentFile(); parent != null; parent = parent.getParentFile()) {
            StructStat directory = Os.lstat(parent.getPath());
            require(OsConstants.S_ISDIR(directory.st_mode) && directory.st_uid == 0 &&
                    (directory.st_mode & 0022) == 0, "Untrusted APK staging ancestor");
        }
        return item;
    }
    public static void main(String[] args) throws Exception {
        require(args.length == 1, "One immutable APK path required");
        require(android.os.Process.myUid() != 0, "APK parsing must run without root authority");
        dalvik.system.VMRuntime.getRuntime().setTargetSdkVersion(29);
        System.load(System.getProperty("saidroid.bridge.library"));
        String nativeRoot = System.getProperty("saidroid.native.root");
        String search = nativeRoot + "/lib64:" + nativeRoot + "/apex/com.android.runtime.debug/lib64:" +
                nativeRoot + "/apex/com.android.conscrypt/lib64:" + nativeRoot + "/apex/com.android.resolv/lib64";
        Class<?> bridge = Class.forName("SdBridge");
        require((Boolean)bridge.getMethod("loadBionicLibrary", String.class, String.class)
                .invoke(null, nativeRoot + "/lib64/libandroid_runtime.so", search), "Native bootstrap failed");
        require((Integer)bridge.getMethod("registerFrameworkNatives").invoke(null) == 100,
                "Matching real framework JNI required");
        Class.forName("SdCryptoProvider").getMethod("install").invoke(null);
        Class.forName("SdTls").getMethod("install").invoke(null);
        File apk = new File(args[0]); StructStat before = staged(apk); String sha = digest(apk);
        PackageParser.Package parsed = new PackageParser().parsePackage(apk, 0);
        PackageParser.collectCertificates(parsed, false);
        require(parsed.mSigningDetails != PackageParser.SigningDetails.UNKNOWN &&
                parsed.mSigningDetails.signatures != null && parsed.mSigningDetails.signatures.length > 0,
                "No genuinely verified APK signers");
        ArrayList<String> signers = new ArrayList<String>();
        for (Signature signature : parsed.mSigningDetails.signatures)
            signers.add(hex(MessageDigest.getInstance("SHA-256").digest(signature.toByteArray())));
        Collections.sort(signers);
        StructStat after = staged(apk);
        require(before.st_dev == after.st_dev && before.st_ino == after.st_ino &&
                before.st_size == after.st_size && sha.equals(digest(apk)), "Staged APK changed during verification");
        JSONObject result = new JSONObject();
        result.put("schema", "saildroid-verified-apk-identity-v1");
        result.put("package", parsed.packageName); result.put("apk_sha256", sha);
        result.put("apk_bytes", before.st_size); result.put("signers", new JSONArray(signers));
        result.put("target_sdk", parsed.applicationInfo.targetSdkVersion);
        result.put("debuggable", (parsed.applicationInfo.flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0);
        result.put("shared_user_id", parsed.mSharedUserId == null ? JSONObject.NULL : parsed.mSharedUserId);
        result.put("verifier_uid", android.os.Process.myUid());
        result.put("application_enabled", parsed.applicationInfo.enabled);
        JSONArray requested = new JSONArray();
        for (String permission : parsed.requestedPermissions) requested.put(permission);
        result.put("requested_permissions", requested);
        JSONArray declared = new JSONArray();
        for (PackageParser.Permission permission : parsed.permissions) {
            JSONObject item = new JSONObject();
            item.put("name", permission.info.name);
            item.put("package", permission.info.packageName);
            item.put("protection_level", permission.info.protectionLevel);
            declared.put(item);
        }
        result.put("declared_permissions", declared);
        JSONArray services = new JSONArray();
        for (PackageParser.Service service : parsed.services) {
            JSONObject item = new JSONObject();
            item.put("name", service.info.name);item.put("package", service.info.packageName);
            item.put("process", service.info.processName);
            item.put("enabled", service.info.enabled);item.put("exported", service.info.exported);
            item.put("permission", service.info.permission == null ? JSONObject.NULL : service.info.permission);
            services.put(item);
        }
        result.put("declared_services", services);
        result.put("backend", "matching-api29-PackageParser.collectCertificates");
        System.out.println("VERIFIED_APK_IDENTITY=" + result.toString());
    }
}
