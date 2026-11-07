#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'cd /tmp
echo "=== 空间检查 ==="
df -h / | tail -1
df -h /tmp | tail -1
echo "=== 清理旧产物 ==="
rm -rf out qqdex 2>/dev/null
mkdir -p out
echo "=== 开始转换全部 40 个 dex（预计 5-8 分钟）==="
cat > QC.java <<EOF
import com.macapk.dex.DexConverter;
import java.util.*;
import java.util.jar.*;
import java.util.zip.*;
import java.io.*;
import java.nio.file.*;

public class QC {
    public static void main(String[] a) throws Exception {
        File apk = new File("/tmp/qq.apk");
        File outJar = new File("/tmp/out/qq.jar");
        Map<String, byte[]> all = new LinkedHashMap<>();
        List<String> dexNames = new ArrayList<>();

        try (ZipFile zf = new ZipFile(apk)) {
            Enumeration<? extends ZipEntry> en = zf.entries();
            while (en.hasMoreElements()) {
                String n = en.nextElement().getName();
                if (n.startsWith("classes") && n.endsWith(".dex")) dexNames.add(n);
            }
        }
        Collections.sort(dexNames);
        System.out.println("QC=dex_count|" + dexNames.size());

        long t0 = System.currentTimeMillis();
        int done = 0;
        try (ZipFile zf = new ZipFile(apk)) {
            for (String dn : dexNames) {
                ZipEntry e = zf.getEntry(dn);
                byte[] dex = zf.getInputStream(e).readAllBytes();
                Map<String, byte[]> m = DexConverter.convert(dex);
                all.putAll(m);
                done++;
                if (done % 5 == 0 || done == dexNames.size()) {
                    long el = (System.currentTimeMillis()-t0)/1000;
                    System.out.println("QC=progress|" + done + "/" + dexNames.size()
                        + "|" + all.size() + "cls|" + el + "s");
                }
            }
        }
        long t1 = System.currentTimeMillis();
        System.out.println("QC=converted|" + all.size() + " classes|" + ((t1-t0)/1000) + "s");

        // 写 jar
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(outJar))) {
            for (Map.Entry<String, byte[]> e : all.entrySet()) {
                jos.putNextEntry(new JarEntry(e.getKey().replace(".", "/") + ".class"));
                jos.write(e.getValue());
                jos.closeEntry();
            }
        }
        System.out.println("QC=jar|" + outJar.length()/1048576 + "MB");
        System.out.println("QC=OK");
    }
}
EOF
/tmp/jdk/bin/javac -cp macapk-loader.jar -d . QC.java 2>&1|head -3
/tmp/jdk/bin/java -Xmx2800m -cp "/tmp:macapk-loader.jar" QC 2>&1 | grep -E "QC=|OutOfMemory|Error" | head -20'
