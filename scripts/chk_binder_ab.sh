JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== 我们 cls 里的 Binder ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.Binder 2>/dev/null | grep -i "asBinder\|class android.os.Binder" | head -5
echo "=== IBinder 接口 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.IBinder 2>/dev/null | grep -i "asBinder\|interface" | head -5
