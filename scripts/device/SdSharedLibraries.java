import android.content.pm.ApplicationInfo;
import android.content.pm.PackageParser;
import java.io.File;
import java.io.FileInputStream;
import java.util.*;
import org.xmlpull.v1.XmlPullParser;

/** Resolve packaged built-in Java libraries from the real platform registry. */
public final class SdSharedLibraries {
    private static final class Library {
        String path; String[] dependencies;
        Library(String path,String dependencies){this.path=path;this.dependencies=dependencies==null?new String[0]:dependencies.split(":");}
    }
    private static Map<String,Library> registry;
    private static synchronized Map<String,Library> registry() {
        if(registry!=null)return registry;
        Map<String,Library> values=new HashMap<String,Library>();
        File root=new File(System.getenv("ANDROID_ROOT"));
        File[] files=new File(root,"system/etc/permissions").listFiles();
        if(files!=null)for(File file:files)if(file.getName().endsWith(".xml"))try(FileInputStream input=new FileInputStream(file)){
            XmlPullParser xml=android.util.Xml.newPullParser();xml.setInput(input,"UTF-8");
            while(xml.next()!=XmlPullParser.END_DOCUMENT)if(xml.getEventType()==XmlPullParser.START_TAG&&"library".equals(xml.getName())){
                String name=xml.getAttributeValue(null,"name"),path=xml.getAttributeValue(null,"file");
                if(name!=null&&path!=null&&path.startsWith("/system/framework/")&&!path.contains("..")){
                    File jar=new File(root,path.substring(1));
                    if(jar.isFile())values.put(name,new Library(jar.getAbsolutePath(),xml.getAttributeValue(null,"dependency")));
                }
            }
        }catch(Exception failure){throw new IllegalStateException("Cannot read platform library registry "+file,failure);}
        registry=values;return registry;
    }
    private static void resolve(String name,LinkedHashSet<String> paths,Set<String> active) {
        Library library=registry().get(name);if(library==null)return;
        if(!active.add(name))throw new IllegalStateException("Cyclic platform library dependency "+name);
        for(String dependency:library.dependencies)resolve(dependency,paths,active);
        paths.add(library.path);active.remove(name);
    }
    public static void apply(ApplicationInfo app,PackageParser.Package pkg) {
        LinkedHashSet<String> paths=new LinkedHashSet<String>();
        // AOSP AndroidTestBaseUpdater / AndroidTestRunnerSplitUpdater rules.
        // This runtime keeps these real platform jars outside the boot path.
        boolean runner=(pkg.usesLibraries!=null&&pkg.usesLibraries.contains("android.test.runner"))||(pkg.usesOptionalLibraries!=null&&pkg.usesOptionalLibraries.contains("android.test.runner"));
        if(app.targetSdkVersion<=28||runner)resolve("android.test.base",paths,new HashSet<String>());
        if(runner)resolve("android.test.mock",paths,new HashSet<String>());
        // AOSP OrgApacheHttpLegacyUpdater: implicit compatibility only for apps
        // targeting before Android P; newer apps need their uses-library entry.
        if(app.targetSdkVersion<28)resolve("org.apache.http.legacy",paths,new HashSet<String>());
        if(pkg.usesLibraries!=null)for(String name:pkg.usesLibraries)resolve(name,paths,new HashSet<String>());
        if(pkg.usesOptionalLibraries!=null)for(String name:pkg.usesOptionalLibraries)resolve(name,paths,new HashSet<String>());
        if(!paths.isEmpty())app.sharedLibraryFiles=paths.toArray(new String[paths.size()]);
    }
}
