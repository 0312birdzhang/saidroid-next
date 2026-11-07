echo "=== cls 目录 ==="
ls /tmp/ap/cls
echo "=== 编译 ViewProbe 的完整输出 ==="
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
W=/tmp/ap
$JAVA/javac --release 8 -nowarn -cp $W/cls:/tmp/fw23/multi.jar -d $W/cls $W/ViewProbe.java 2>&1 | head -25
ls -l $W/cls/ViewProbe*.class 2>/dev/null | head -5
