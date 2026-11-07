JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== IDisplayManager 方法 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.hardware.display.IDisplayManager 2>/dev/null | head -30
echo "=== DisplayManagerGlobal 的字段 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.hardware.display.DisplayManagerGlobal 2>/dev/null | head -25
