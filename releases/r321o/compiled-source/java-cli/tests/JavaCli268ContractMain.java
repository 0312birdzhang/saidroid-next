import java.io.*;
import java.nio.file.*;
import java.util.*;
public final class JavaCli268ContractMain {
 public static void main(String[]args)throws Exception {
  if(args.length!=3||!args[0].equals("hello space")||!args[1].equals("中文"))throw new AssertionError("CLI Java argument preservation");
  int uid=android.system.Os.getuid();if(uid==0)throw new AssertionError("ordinary caller UID required");
  // App code must not acquire the platform's private runtime APIs.
  try{Class.forName("dalvik.system.VMRuntime").getDeclaredMethod("setHiddenApiExemptions",String[].class);throw new AssertionError("CLI application hidden API exposed");}
  catch(NoSuchMethodException expected){}
  String status=new String(Files.readAllBytes(Paths.get("/proc/self/status")),"UTF-8");
  for(String line:status.split("\n"))if(line.startsWith("CapEff:")&&!line.trim().endsWith("0000000000000000"))throw new AssertionError("effective capabilities");
  if(!status.matches("(?s).*NoNewPrivs:\\s+1\\n.*"))throw new AssertionError("no_new_privs");
  String text=new BufferedReader(new InputStreamReader(System.in,"UTF-8")).readLine();if(!"stdin payload".equals(text))throw new AssertionError("real stdin pipe");
  Path dir=Paths.get(args[2]),file=dir.resolve("child-owned.txt"),link=dir.resolve("forbidden-link.txt");Files.write(file,"child-private-data".getBytes("UTF-8"));
  if(!new String(Files.readAllBytes(file),"UTF-8").equals("child-private-data"))throw new AssertionError("real file IO");
  try{Files.createLink(link,file);throw new AssertionError("app filesystem hardlink policy lost");}catch(java.nio.file.AccessDeniedException expected){}
  String maps=new String(Files.readAllBytes(Paths.get("/proc/self/maps")),"UTF-8");String root=System.getenv("ANDROID_ROOT");
  Set<String> arts=new HashSet<>(),images=new HashSet<>(),cores=new HashSet<>();
  for(String line:maps.split("\n")){String[]part=line.trim().split(" +");String path=part[part.length-1];if(path.endsWith("/libart.so"))arts.add(path);if(path.endsWith(".art"))images.add(path);if(path.endsWith("/libjavacore.so"))cores.add(path);}
  if(!arts.equals(Collections.singleton(root+"/lib/libart.so"))||images.size()!=9||!cores.equals(Collections.singleton(root+"/lib/libjavacore.so")))throw new AssertionError("actual component ART/JNI/9images: "+arts+images+cores);
  for(String image:images)if(!image.startsWith(root+"/system/framework/arm64/"))throw new AssertionError("foreign boot image");
  if(!maps.contains(root+"/lib/libsdmath-precision.so")||!maps.contains(root+"/lib/libsdcharacter-icu63.so"))throw new AssertionError("actual private native dependencies");
  if(!java.text.Normalizer.normalize("e\u0301",java.text.Normalizer.Form.NFC).equals("\u00e9"))throw new AssertionError("actual native Unicode normalization");
  if(Double.doubleToRawLongBits(Math.tan(1.0))!=Double.doubleToRawLongBits(StrictMath.tan(1.0)))throw new AssertionError("actual nativeMath backend");
  System.out.println("JAVA_CLI268_CONTRACT=PASS|uid="+uid+"|hidden_api=denied|images=9|actual_component_native=true|stdio=true|app_policy=true|exit=23");
  System.err.println("JAVA_CLI268_STDERR=actual-java");System.exit(23);
 }
}
