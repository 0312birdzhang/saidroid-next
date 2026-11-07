#!/bin/bash
export JAVA_HOME=/opt/art/jdk
export PATH=$JAVA_HOME/bin:/opt/art/bin:$PATH
export LD_LIBRARY_PATH=/opt/art/lib/aarch64-linux-gnu:/opt/art/lib
export ANDROID_DATA=/tmp/art-data
export ANDROID_ROOT=/opt/art
mkdir -p $ANDROID_DATA

echo "=== 检查 bootclasspath ==="
ls /opt/art/java/dex/art/*.jar 2>/dev/null | head -5

echo "=== 跑 Hello World ==="
cd /tmp/hello 2>/dev/null || { mkdir -p /tmp/hello && cd /tmp/hello; }
cat > Hello.java <<'EOF'
public class Hello {
    public static void main(String[] a) {
        System.out.println("OPTART_HELLO");
        long s = 0;
        for (int i = 1; i <= 100; i++) s += i;
        System.out.println("sum=" + s);
    }
}
EOF
$JAVA_HOME/bin/javac --release 8 Hello.java 2>/dev/null
/opt/art/bin/dx --dex --output=hello.dex . 2>/dev/null
ls -la hello.dex 2>/dev/null
/opt/art/bin/dalvikvm -cp hello.dex Hello 2>&1 | head -12
