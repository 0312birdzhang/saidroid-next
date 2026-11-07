#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
BASE=/tmp/art-build/art-standalone
export LD_LIBRARY_PATH=$BASE/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/dalvik-data
export ANDROID_ROOT=$BASE/out/host/linux-x86
mkdir -p $ANDROID_DATA
BCP="$BASE/out/host/linux-x86/framework/core-oj-hostdex.jar:$BASE/out/host/linux-x86/framework/core-libart-hostdex.jar"

echo "=== 测试1: 算术与字符串 ==="
cat > /tmp/hello/T1.java <<'EOF'
public class T1 {
    public static void main(String[] a) {
        System.out.println("ART_TEST_1_START");
        long s = 0;
        for (int i = 1; i <= 1000; i++) s += i;
        System.out.println("sum_1_to_1000=" + s);
        String str = "concatenation";
        System.out.println("string_len=" + str.length());
        int[] arr = new int[100];
        for (int i = 0; i < 100; i++) arr[i] = i * i;
        System.out.println("arr_99=" + arr[99]);
        System.out.println("ART_TEST_1_OK");
    }
}
EOF
cd /tmp/hello
$JAVA_HOME/bin/javac --release 8 T1.java 2>/dev/null
$BASE/out/host/linux-x86/bin/dx --dex --output=t1.dex . 2>/dev/null
$BASE/out/host/linux-x86/bin/dalvikvm -Xbootclasspath:"$BCP" -cp t1.dex T1 2>&1 | grep -E "ART_TEST|sum_|string_len|arr_99"

echo
echo "=== 测试2: 异常处理 ==="
cat > /tmp/hello/T2.java <<'EOF'
public class T2 {
    public static void main(String[] a) {
        System.out.println("ART_TEST_2_START");
        try {
            int x = 1 / 0;
            System.out.println("should_not_reach=" + x);
        } catch (ArithmeticException e) {
            System.out.println("caught=" + e.getClass().getSimpleName());
        }
        System.out.println("ART_TEST_2_OK");
    }
}
EOF
$JAVA_HOME/bin/javac --release 8 T2.java 2>/dev/null
$BASE/out/host/linux-x86/bin/dx --dex --output=t2.dex . 2>/dev/null
$BASE/out/host/linux-x86/bin/dalvikvm -Xbootclasspath:"$BCP" -cp t2.dex T2 2>&1 | grep -E "ART_TEST|caught="
