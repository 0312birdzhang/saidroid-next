#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'cd /tmp
rm -rf qqdex 2>/dev/null
mkdir -p qqdex && cd qqdex
echo "=== 提取前几个 dex ==="
/tmp/jdk/bin/jar xf /tmp/qq.apk classes.dex 2>/dev/null
ls -la *.dex 2>/dev/null
cd /tmp
cat > QS.java <<EOF
import com.macapk.dex.DexConverter;
import java.nio.file.*;
import java.util.*;
public class QS {
    public static void main(String[] a) throws Exception {
        byte[] dex = Files.readAllBytes(Paths.get("/tmp/qqdex/classes.dex"));
        Map<String, byte[]> m = DexConverter.convert(dex);
        System.out.println("QS=classes|" + m.size());
        // 找 SplashActivity
        for (String k : m.keySet()) {
            if (k.contains("SplashActivity")) {
                System.out.println("QS=found|" + k);
                Files.write(Paths.get("/tmp/splash.class"), m.get(k));
            }
        }
    }
}
EOF
/tmp/jdk/bin/javac -cp macapk-loader.jar -d . QS.java 2>&1|head -3
/tmp/jdk/bin/java -Xmx2500m -cp "/tmp:macapk-loader.jar" QS 2>&1 | grep QS | head -8
echo "=== 反编译看构造 ==="
ls -la /tmp/splash.class 2>/dev/null && /tmp/jdk/bin/javap -p /tmp/splash.class 2>/dev/null | grep -E "SplashActivity\(|class SplashActivity" | head -5'
