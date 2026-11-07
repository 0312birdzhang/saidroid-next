JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
echo "=== Display\$Mode 构造器 ==="
$JAVA/javap -p -classpath /tmp/fw23/cls 'android.view.Display$Mode' 2>/dev/null | grep -E "Mode\(|public" | head -8
echo "=== Display 的 ColorTransform ==="
$JAVA/javap -p -classpath /tmp/fw23/cls 'android.view.Display$ColorTransform' 2>/dev/null | grep -E "ColorTransform\(|getR\(|length" | head -6
echo "=== 设备上 libmmkv ==="
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@bonito "ls -l /home/art/realapps/qq-libs/ | grep -i mmkv; ls /home/art/realapps/qq-libs/ | wc -l"
