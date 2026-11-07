"""Exercise real filesystem boundaries of the Java cache registration helper.

Minimal framework/bridge declarations capture registrations; they never stand
in for Android execution. The phone's original ScriptC test is the real loader
acceptance gate.
"""
from pathlib import Path
import os,subprocess,tempfile
repo=Path(__file__).resolve().parents[3]
java=Path(os.environ.get('JAVA_HOME','/tmp/jdkfull/jdk-21.0.13+9'))/'bin'
with tempfile.TemporaryDirectory(prefix='sd-code-cache-')as directory:
 out=Path(directory);package=out/'android/content/pm';package.mkdir(parents=True)
 (package/'ApplicationInfo.java').write_text('package android.content.pm;public class ApplicationInfo{public String dataDir,deviceProtectedDataDir,packageName;}')
 (out/'SdBridge.java').write_text('import java.util.*;public class SdBridge{public static ArrayList<String> calls=new ArrayList<>();public static boolean addBionicLibraryPath(String value){calls.add(value);return true;}}')
 (out/'dalvik/system').mkdir(parents=True)
 (out/'dalvik/system/BaseDexClassLoader.java').write_text('package dalvik.system;public class BaseDexClassLoader extends ClassLoader{}')
 (out/'Check.java').write_text(r'''
import java.io.*;import java.nio.file.*;import android.content.pm.ApplicationInfo;
public class Check{
 public static void main(String[]args)throws Exception{
  Path root=Paths.get(args[0]);ApplicationInfo a=new ApplicationInfo();a.packageName="fixture";
  a.dataDir=root.resolve("app").toString();a.deviceProtectedDataDir=root.resolve("app/device-protected").toString();
  SdClassLoaderNamespaces.registerApplicationCodeCache(a);
  if(SdBridge.calls.size()!=1)throw new AssertionError();
  String[] actual=SdBridge.calls.get(0).split(File.pathSeparator);
  java.util.HashSet<String> expectedPaths=new java.util.HashSet<String>();
  for(String location:new String[]{"app/code_cache","app/cache","app/device-protected/code_cache","app/device-protected/cache"}){
   Path cache=root.resolve(location);if(!Files.isDirectory(cache))throw new AssertionError();
   expectedPaths.add(cache.toString());expectedPaths.add(cache.toString()+"/*");
  }
  if(actual.length!=8||!expectedPaths.equals(new java.util.HashSet<String>(java.util.Arrays.asList(actual))))throw new AssertionError();
  a.deviceProtectedDataDir=root.resolve("outside").toString();
  try{SdClassLoaderNamespaces.registerApplicationCodeCache(a);throw new AssertionError("escaped device path accepted");}catch(SecurityException expected){}
  a.dataDir=root.resolve("linkedapp").toString();a.deviceProtectedDataDir=null;
  Files.createDirectories(root.resolve("linkedapp"));Files.createDirectories(root.resolve("outside"));Files.createSymbolicLink(root.resolve("linkedapp/code_cache"),root.resolve("outside"));
  try{SdClassLoaderNamespaces.registerApplicationCodeCache(a);throw new AssertionError("symlink cache accepted");}catch(SecurityException expected){}
  if(SdBridge.calls.size()!=1)throw new AssertionError("rejected paths mutated loader registration");
  System.out.println("CODE_CACHE_BOUNDARY=PASS|normal_cache_directories=4|atomic_registration=true|escaped_device=rejected|symlink_escape=rejected");
 }
}
''')
 sources=[*out.rglob('*.java'),repo/'scripts/device/SdClassLoaderNamespaces.java']
 subprocess.run([str(java/'javac'),'-d',str(out),*[str(p)for p in sources]],check=True)
 subprocess.run([str(java/'java'),'-cp',str(out),'Check',str(out/'files')],check=True,timeout=10)
