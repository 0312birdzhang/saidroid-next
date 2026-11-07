import android.content.pm.PermissionInfo;
import android.content.res.AssetManager;
import android.content.res.XmlResourceParser;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import org.xmlpull.v1.XmlPullParser;

/** Narrow local-app grants derived from the actual binary APK manifest.
 * Host permissions and permissions owned by other packages are not inferred.
 */
public final class SdAppPermissions {
    private final String owner;
    private static final String ANDROID = "http://schemas.android.com/apk/res/android";
    private final Map<String, Integer> declarations = new HashMap<String, Integer>();
    private final Map<String, Integer> platformDeclarations = new HashMap<String, Integer>();
    private final Set<String> requested = new HashSet<String>();

    public SdAppPermissions(String apk, String expectedPackage) throws Exception {
        owner=expectedPackage;
        readManifest(apk, expectedPackage, declarations, true);
        readManifest(System.getenv("ANDROID_ROOT")+"/framework/framework-res.apk", "android", platformDeclarations, false);
    }

    private void readManifest(String apk, String expectedPackage, Map<String, Integer> target,
                              boolean collectRequested) throws Exception {
        if (apk == null) throw new IllegalArgumentException("APK path is required");
        AssetManager assets = new AssetManager();
        XmlResourceParser xml = null;
        try {
            int cookie = assets.addAssetPath(apk);
            if (cookie == 0) throw new IllegalArgumentException("Cannot read APK: " + apk);
            xml = assets.openXmlResourceParser(cookie, "AndroidManifest.xml");
            boolean verified = false;
            for (int event = xml.next(); event != XmlPullParser.END_DOCUMENT; event = xml.next()) {
                if (event != XmlPullParser.START_TAG) continue;
                String tag = xml.getName();
                if (xml.getDepth() == 1 && "manifest".equals(tag)) {
                    if (!expectedPackage.equals(xml.getAttributeValue(null, "package"))) {
                        throw new SecurityException("Manifest package differs from the bound owner");
                    }
                    verified = true;
                }
                if (xml.getDepth() != 2) continue;
                String name = xml.getAttributeValue(ANDROID, "name");
                if (name == null) continue;
                if ("permission".equals(tag)) {
                    target.put(name, xml.getAttributeIntValue(ANDROID, "protectionLevel", 0));
                } else if (collectRequested && ("uses-permission".equals(tag)
                        || "uses-permission-sdk-23".equals(tag) || "uses-permission-sdk-m".equals(tag))) {
                    int maxSdk = xml.getAttributeIntValue(ANDROID, "maxSdkVersion", Integer.MAX_VALUE);
                    if (maxSdk >= android.os.Build.VERSION.SDK_INT) requested.add(name);
                }
            }
            if (!verified) throw new SecurityException("Missing manifest identity");
        } finally {
            if (xml != null) xml.close();
            assets.close();
        }
    }

    public boolean holds(String permission) {
        if (permission == null) return true;
        if (!requested.contains(permission)) return false;
        Integer protection = declarations.get(permission);
        if (protection == null) {
            protection = platformDeclarations.get(permission);
            // Android automatically grants requested normal permissions. Its
            // dangerous/signature permissions need an explicit grant/signature
            // backend and are never inferred from package existence.
            return protection != null && ((protection & PermissionInfo.PROTECTION_MASK_BASE)
                    == PermissionInfo.PROTECTION_NORMAL || ((protection & PermissionInfo.PROTECTION_MASK_BASE)
                    == PermissionInfo.PROTECTION_DANGEROUS && "granted".equals(decisions().getProperty(permission))));
        }
        int base = protection & PermissionInfo.PROTECTION_MASK_BASE;
        // The single hosted app is also the declaring/signing owner. This does
        // not confer signature privileges owned by android or another APK.
        return base == PermissionInfo.PROTECTION_NORMAL || base == PermissionInfo.PROTECTION_SIGNATURE;
    }

    private java.io.File decisionFile(){
        if(!SdApkPackage.NAME.equals(owner))throw new SecurityException("Runtime grant owner differs");
        return new java.io.File(SdApkPackage.DATA,"saildroid-runtime-permissions.properties");
    }
    private java.util.Properties decisions(){
        java.util.Properties result=new java.util.Properties();
        if(!SdApkPackage.NAME.equals(owner))return result;
        java.io.File path=decisionFile();
        if(path.isFile())try(java.io.FileInputStream input=new java.io.FileInputStream(path)){result.load(input);}
        catch(java.io.IOException failure){throw new IllegalStateException("Cannot read runtime grants",failure);}
        return result;
    }
    public boolean canRequest(String name){
        Integer flags=platformDeclarations.get(name);
        return requested.contains(name)&&flags!=null&&(flags&PermissionInfo.PROTECTION_MASK_BASE)==PermissionInfo.PROTECTION_DANGEROUS;
    }
    public boolean supported(String name){
        if(!canRequest(name))return false;
        if(name.equals("android.permission.CAMERA"))return SdCamera.available();
        if(!name.equals("android.permission.READ_EXTERNAL_STORAGE")&&!name.equals("android.permission.WRITE_EXTERNAL_STORAGE"))return false;
        String root=System.getenv("EXTERNAL_STORAGE");
        return root!=null&&new java.io.File(root).isDirectory()&&new java.io.File(root).canRead()
                &&(!name.equals("android.permission.WRITE_EXTERNAL_STORAGE")||new java.io.File(root).canWrite());
    }
    public boolean shouldShowRationale(String name){return canRequest(name)&&!holds(name)&&"denied".equals(decisions().getProperty(name));}
    public synchronized void decide(String name,boolean grant){
        if(!canRequest(name))return;
        if(grant&&!supported(name))throw new SecurityException("Permission backend is unavailable");
        java.util.Properties state=decisions();state.setProperty(name,grant?"granted":"denied");
        java.io.File path=decisionFile(),temporary=new java.io.File(path.getPath()+".tmp");
        try(java.io.FileOutputStream output=new java.io.FileOutputStream(temporary)){state.store(output,"Explicit per-application SailDroid runtime permission choices");output.getFD().sync();}
        catch(java.io.IOException failure){throw new IllegalStateException("Cannot save runtime permission decision",failure);}
        if(!temporary.renameTo(path))throw new IllegalStateException("Cannot publish runtime permission decision");
    }

    public Set<String> getOwnedGrants() {
        Set<String> result = new HashSet<String>();
        for (String name : declarations.keySet()) if (holds(name)) result.add(name);
        return java.util.Collections.unmodifiableSet(result);
    }
}
