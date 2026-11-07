#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'cd /tmp
echo "=== 清理空间 ==="
rm -rf out 2>/dev/null
df -h /tmp | tail -1
echo "=== 只转换第一个 dex（10.5 MB）测可行性 ==="
mkdir -p qqdex && cd qqdex
/tmp/jdk/bin/jar xf /tmp/qq.apk classes.dex 2>/dev/null || /tmp/jdk/bin/jar xf /tmp/qq.apk 2>/dev/null
ls -la classes.dex 2>/dev/null
cd /tmp
cat > QD.java <<EOF
import com.macapk.dex.DexConverter;
import java.nio.file.*;
import java.util.*;
public class QD {
    public static void main(String[] a) throws Exception {
        byte[] dex = Files.readAllBytes(Paths.get("/tmp/qqdex/classes.dex"));
        System.out.println("QD=input|" + dex.length);
        long t0 = System.currentTimeMillis();
        Map<String, byte[]> m = DexConverter.convert(dex);
        long t1 = System.currentTimeMillis();
        System.out.println("QD=converted|" + m.size() + " classes|" + (t1-t0) + "ms");
        System.out.println("QD=MEM|" + (Runtime.getRuntime().totalMemory()/1048576) + "MB");
    }
}
EOF
/tmp/jdk/bin/javac -cp macapk-loader.jar -d . QD.java 2>&1|head -3
/tmp/jdk/bin/java -Xmx2g -cp "/tmp:macapk-loader.jar" QD 2>&1 | grep -E "QD=|Error|Exception" | head -8'
