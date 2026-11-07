JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== IWindowManager 方法数 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.view.IWindowManager 2>/dev/null | grep -c "abstract"
echo "=== 前 12 个 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.view.IWindowManager 2>/dev/null | grep abstract | head -12
