#!/bin/bash
cd /tmp/art-build/art-standalone
export LD_LIBRARY_PATH=/tmp/art-build/art-standalone/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/dalvik-data
mkdir -p $ANDROID_DATA

echo "=== 用 dx 把一个 Java class 转成 dex ==="
mkdir -p /tmp/hello && cd /tmp/hello
cat > Hello.java <<'EOF'
public class Hello {
    public static void main(String[] args) {
        System.out.println("HELLO_FROM_ART");
        int x = 0;
        for (int i = 0; i < 100000; i++) x += i;
        System.out.println("sum=" + x);
    }
}
EOF
/tmp/jdkfull/jdk-21.0.13+9/bin/javac Hello.java 2>&1 | head -3
ls -la Hello.class 2>/dev/null
echo "=== dx 转换 ==="
/tmp/art-build/art-standalone/out/host/linux-x86/bin/dx --dex --output=hello.dex . 2>&1 | head -5
ls -la hello.dex 2>/dev/null
echo "=== 用 dalvikvm 执行 ==="
cd /tmp/hello
/tmp/art-build/art-standalone/out/host/linux-x86/bin/dalvikvm -cp hello.dex Hello 2>&1 | head -10
