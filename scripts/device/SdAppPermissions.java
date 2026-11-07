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
    private static final String ANDROID = "http://schemas.android.com/apk/res/android";
    private final Map<String, Integer> declarations = new HashMap<String, Integer>();
    private final Map<String, Integer> platformDeclarations = new HashMap<String, Integer>();
    private final Set<String> requested = new HashSet<String>();

    public SdAppPermissions(String apk, String expectedPackage) throws Exception {
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
            return protection != null && (protection & PermissionInfo.PROTECTION_MASK_BASE)
                    == PermissionInfo.PROTECTION_NORMAL;
        }
        int base = protection & PermissionInfo.PROTECTION_MASK_BASE;
        // The single hosted app is also the declaring/signing owner. This does
        // not confer signature privileges owned by android or another APK.
        return base == PermissionInfo.PROTECTION_NORMAL || base == PermissionInfo.PROTECTION_SIGNATURE;
    }

    public Set<String> getOwnedGrants() {
        Set<String> result = new HashSet<String>();
        for (String name : declarations.keySet()) if (holds(name)) result.add(name);
        return java.util.Collections.unmodifiableSet(result);
    }
}
