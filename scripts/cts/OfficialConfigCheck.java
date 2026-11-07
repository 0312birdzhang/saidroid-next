import com.android.tradefed.config.ConfigurationFactory;
import com.android.tradefed.config.IConfiguration;
import java.nio.file.*;
import java.util.*;
import java.io.*;
import com.google.gson.*;
/** Executes official config constructors/validation; does not certify tests. */
public final class OfficialConfigCheck {
 public static void main(String[] args)throws Exception{
  Path configs=Paths.get(args[0]),output=Paths.get(args[1]);JsonArray rows=new JsonArray();int passed=0,failed=0;
  try(java.util.stream.Stream<Path> files=Files.list(configs)){
   for(Path path:(Iterable<Path>)files.filter(p->p.toString().endsWith(".config")).sorted()::iterator){
    JsonObject row=new JsonObject();row.addProperty("module",path.getFileName().toString().replace(".config",""));
    try{
     IConfiguration config=ConfigurationFactory.getInstance().createConfigurationFromArgs(new String[]{path.toString()});
     JsonArray tests=new JsonArray();for(Object test:config.getTests())tests.add(test.getClass().getName());row.add("official_test_objects",tests);
     JsonArray preparers=new JsonArray();for(Object prep:config.getTargetPreparers())preparers.add(prep.getClass().getName());row.add("official_preparer_objects",preparers);
     config.validateOptions(false);row.addProperty("status","CONFIG_VALIDATED");passed++;
    }catch(Throwable problem){row.addProperty("status","CONFIG_ERROR");StringWriter stack=new StringWriter();problem.printStackTrace(new PrintWriter(stack));row.addProperty("error",stack.toString());failed++;}
    rows.add(row);
   }
  }
  JsonObject result=new JsonObject();result.addProperty("scope","official-configuration-loading-not-module-test-results");result.addProperty("configs",rows.size());result.addProperty("validated",passed);result.addProperty("errors",failed);result.add("modules",rows);Files.write(output,new GsonBuilder().setPrettyPrinting().create().toJson(result).getBytes("UTF-8"));
  System.out.println("OFFICIAL_CONFIG_CHECK=configs:"+rows.size()+"|validated:"+passed+"|errors:"+failed);
 }
}
