export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15 '
  echo "== lock"; ls -ld /home/art/test/.device-lock 2>/dev/null && cat /home/art/test/.device-lock/* 2>/dev/null | head -5 || echo "NO_LOCK"
  echo "== release"; readlink -f /home/art/api29-root
  echo "== wayland-server"; ls -l /usr/lib64/libwayland-server.so.0* 2>/dev/null | head -3
  echo "== wpe procs"; pgrep -a -f "WPEWebProcess|atlantic|wpe" | head -5 || echo none
' 2>&1
