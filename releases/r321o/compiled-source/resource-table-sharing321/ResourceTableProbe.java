import android.content.res.Resources;
import android.content.res.XmlResourceParser;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
public class ResourceTableProbe {
 static void snapshot(Path target)throws Exception {Files.write(target,Files.readAllBytes(Paths.get("/proc/self/smaps")));}
 public static void main(String[] args)throws Exception {
  Path dir=Paths.get(args[0]);String id=args[1];
  if(ResourceTableProbe.class.getClassLoader()==Object.class.getClassLoader())throw new AssertionError("App domain");
  snapshot(dir.resolve(id+"-before.smaps"));
  long start=System.nanoTime();Resources r=Resources.getSystem();StringBuilder values=new StringBuilder();
  int[] strings={android.R.string.ok,android.R.string.cancel,android.R.string.yes,android.R.string.no,android.R.string.copy,android.R.string.paste,android.R.string.selectAll};
  for(int n:strings)values.append(r.getResourceName(n)).append('=').append(r.getString(n)).append('\n');
  values.append("white=").append(r.getColor(android.R.color.white)).append(" black=").append(r.getColor(android.R.color.black)).append('\n');
  values.append("icon=").append(r.getDimensionPixelSize(android.R.dimen.app_icon_size)).append('\n');
  XmlResourceParser parser=r.getXml(android.R.layout.simple_list_item_1);int events=0;
  while(parser.next()!=org.xmlpull.v1.XmlPullParser.END_DOCUMENT){events++;if(parser.getEventType()==org.xmlpull.v1.XmlPullParser.START_TAG)values.append("xml=").append(parser.getName()).append('\n');}parser.close();
  if(events<2)throw new AssertionError("XML empty");
  int denied=0;try{Class.forName("dalvik.system.VMRuntime").getDeclaredMethod("setHiddenApiExemptions",String[].class);}catch(NoSuchMethodException e){denied|=1;}
  try{Class.forName("dalvik.system.VMDebug").getDeclaredMethod("attachAgent",String.class,ClassLoader.class);}catch(NoSuchMethodException e){denied|=2;}if(denied!=3)throw new AssertionError("Hidden API policy");
  Files.write(dir.resolve(id+"-values.txt"),values.toString().getBytes(StandardCharsets.UTF_8));
  Files.write(dir.resolve(id+"-ready"),("elapsed_ns="+(System.nanoTime()-start)+" hidden_api_denied=3\n").getBytes(StandardCharsets.UTF_8));
  long deadline=System.nanoTime()+15000000000L;while(!Files.exists(dir.resolve("capture"))){if(System.nanoTime()>deadline)throw new AssertionError("capture timeout");Thread.sleep(20);}
  snapshot(dir.resolve(id+"-after.smaps"));Files.write(dir.resolve(id+"-captured"),new byte[]{1});
  while(!Files.exists(dir.resolve("finish"))){if(System.nanoTime()>deadline)throw new AssertionError("finish timeout");Thread.sleep(20);}
  System.out.println("RESOURCE_TABLE_PROBE=passed|xml_events="+events+"|hidden_api_denied=3|app_domain=untrusted");
 }
}
