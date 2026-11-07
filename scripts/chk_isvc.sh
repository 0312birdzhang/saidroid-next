JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
ls /tmp/fw23/cls/android/os/IServiceManager*.class 2>/dev/null
echo "=== 类里有什么嵌套类 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls 'android.os.IServiceManager$Stub' 2>&1 | head -6
