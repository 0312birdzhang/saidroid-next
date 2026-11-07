JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== IPackageManager 方法数 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.content.pm.IPackageManager 2>/dev/null | grep -c "abstract"
echo "=== 前 8 个 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls android.content.pm.IPackageManager 2>/dev/null | grep abstract | head -8
echo "=== 设备上 QQ native libs ==="
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@bonito "ls -d /home/art/realapps/qq-libs 2>/dev/null && ls /home/art/realapps/qq-libs | head -5; ls /home/art/realapps/qq/*.so 2>/dev/null | head -3"
