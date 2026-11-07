#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'cd /tmp
echo "=== 清理 ==="
rm -rf qqdex out 2>/dev/null
echo "=== 逐个 dex 转换（测内存峰值）==="
mkdir -p qqdex && cd qqdex
/tmp/jdk/bin/jar xf /tmp/qq.apk classes.dex classes2.dex classes3.dex 2>/dev/null
ls -la *.dex 2>/dev/null
cd /tmp
cat > QM.java <<EOF
import com.macapk.dex.DexConverter;
import java.nio.file.*;
import java.util.*;
public class QM {
    public static void main(String[] a) throws Exception {
        String[] files = {"classes.dex","classes2.dex","classes3.dex"};
        long total = 0; int totalCls = 0;
        for (String f : files) {
            Path p = Paths.get("/tmp/qqdex/" + f);
            if (!Files.exists(p)) continue;
            byte[] dex = Files.readAllBytes(p);
            long t0 = System.currentTimeMillis();
            Map<String, byte[]> m = DexConverter.convert(dex);
            long t1 = System.currentTimeMillis();
            Runtime rt = Runtime.getRuntime();
            long used = (rt.totalMemory() - rt.freeMemory()) / 1048576;
            System.out.println("QM=" + f + "|" + dex.length/1048576 + "MB|" + m.size() + "cls|" + (t1-t0) + "ms|used=" + used + "MB");
            total += dex.length; totalCls += m.size();
            m = null;
            System.gc();
        }
        System.out.println("QM=total|" + total/1048576 + "MB|" + totalCls + "cls");
    }
}
EOF
/tmp/jdk/bin/javac -cp macapk-loader.jar -d . QM.java 2>&1|head -3
/tmp/jdk/bin/java -Xmx2500m -cp "/tmp:macapk-loader.jar" QM 2>&1 | grep -E "QM=|OutOfMemory" | head -8'
