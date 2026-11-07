import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import com.google.gson.*;

/** Official ddmlib reads actual retained phone stdout, including failures. */
public final class OfficialInstrumentationProtocolCheck {
    public static void main(String[] args) throws Exception {
        Map<String, Integer> counts = new LinkedHashMap<>();
        List<String> failures = new ArrayList<>();
        List<String> runFailures = new ArrayList<>();
        boolean[] ended = {false};
        Class<?> listenerType = Class.forName("com.android.ddmlib.testrunner.ITestRunListener");
        Object listener = Proxy.newProxyInstance(listenerType.getClassLoader(),
                new Class<?>[]{listenerType}, (proxy, method, values) -> {
                    String name = method.getName();
                    if (name.equals("toString")) return "RetainedPhoneProtocolListener";
                    if (name.equals("hashCode")) return System.identityHashCode(proxy);
                    if (name.equals("equals")) return proxy == values[0];
                    counts.put(name, counts.getOrDefault(name, 0) + 1);
                    if (name.equals("testFailed")) failures.add(String.valueOf(values[0]));
                    if (name.equals("testRunFailed")) runFailures.add(String.valueOf(values[0]));
                    if (name.equals("testRunEnded")) ended[0] = true;
                    return null;
                });
        Class<?> parserType = Class.forName("com.android.ddmlib.testrunner.InstrumentationResultParser");
        Object parser = parserType.getConstructor(String.class, listenerType)
                .newInstance("actual-retained-phone-" + args[2], listener);
        byte[] bytes = Files.readAllBytes(Paths.get(args[0]));
        Method add = parserType.getMethod("addOutput", byte[].class, int.class, int.class);
        for (int offset = 0; offset < bytes.length; offset += 4093)
            add.invoke(parser, bytes, offset, Math.min(4093, bytes.length - offset));
        parserType.getMethod("flush").invoke(parser);
        JsonObject result = new JsonObject();
        result.addProperty("scope", "Official unchanged ddmlib parsing actual retained phone stdout; offline protocol check, no new CTS execution");
        result.addProperty("case", args[2]);
        result.add("callbacks", new Gson().toJsonTree(counts));
        result.add("failed_tests", new Gson().toJsonTree(failures));
        result.add("run_failures", new Gson().toJsonTree(runFailures));
        result.addProperty("run_ended", ended[0]);
        boolean passed = ended[0] && runFailures.isEmpty()
                && counts.getOrDefault("testStarted", 0) == 596
                && counts.getOrDefault("testEnded", 0) == 596
                && failures.size() == Integer.parseInt(args[3]);
        result.addProperty("passed", passed);
        Files.write(Paths.get(args[1]), new GsonBuilder().setPrettyPrinting().create()
                .toJson(result).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        System.out.println(result);
        if (!passed) throw new AssertionError("Official result parser did not retain actual outcomes");
    }
}
