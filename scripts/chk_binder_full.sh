JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== Binder 全部方法（找 asBinder）==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.os.Binder 2>/dev/null | sed -n '1,40p'
