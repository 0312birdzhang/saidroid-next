export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
echo "=== lipstick 相关 bus 名 ==="
$SSH "dbus-send --system --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.ListNames 2>/dev/null | grep -i 'lipstick\|screenshot\|screen' | head -8"
echo "=== 已知截图路径试探 ==="
for p in /org/nemomobile/lipstick /org/nemomobile/lipstick/screenshot /com/jolla/lipstick; do
  echo "--- $p ---"
  $SSH "dbus-send --system --print-reply --dest=org.nemomobile.lipstick $p org.freedesktop.DBus.Introspectable.Introspect 2>&1 | grep -i 'method name' | head -6"
done
echo "=== 音量键设备 ==="
$SSH "ls /dev/input/ | head -8"
