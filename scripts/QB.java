import com.macapk.dex.DexConverter;
import java.util.*;
import java.util.jar.*;
import java.util.zip.*;
import java.io.*;

public class QB {
    public static void main(String[] a) throws Exception {
        int batchSize = Integer.parseInt(a[0]);
        int startFrom = a.length > 1 ? Integer.parseInt(a[1]) : 0;
        File apk = new File("/tmp/qq.apk");
        List<String> names = new ArrayList<>();
        try (ZipFile zf = new ZipFile(apk)) {
            Enumeration<? extends ZipEntry> en = zf.entries();
            while (en.hasMoreElements()) {
                String n = en.nextElement().getName();
                if (n.startsWith("classes") && n.endsWith(".dex")) names.add(n);
            }
        }
        Collections.sort(names);
        int total = names.size();
        int done = 0, totalCls = 0;

        for (int b = startFrom; b < total; b += batchSize) {
            int end = Math.min(b + batchSize, total);
            File part = new File("/tmp/out/part" + (b/batchSize) + ".jar");
            Map<String, byte[]> m = new LinkedHashMap<>();
            try (ZipFile zf = new ZipFile(apk)) {
                for (int i = b; i < end; i++) {
                    byte[] dex = zf.getInputStream(zf.getEntry(names.get(i))).readAllBytes();
                    m.putAll(DexConverter.convert(dex));
                }
            }
            try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(part))) {
                for (Map.Entry<String, byte[]> e : m.entrySet()) {
                    jos.putNextEntry(new JarEntry(e.getKey().replace(".", "/") + ".class"));
                    jos.write(e.getValue());
                    jos.closeEntry();
                }
            }
            done += (end - b);
            totalCls += m.size();
            System.out.println("QB=batch|" + done + "/" + total + "|" + totalCls + "cls|"
                + part.getName() + "|" + part.length()/1048576 + "MB");
            m = null;
            System.gc();
            Thread.sleep(800);
        }
        System.out.println("QB=OK|" + totalCls + " classes");
    }
}
