#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "=== 清理前 ==="
$SSH "pgrep -af 'atlantic-browser|WPEWebProcess' | cut -c1-120"
echo "=== 只杀 --help 探针链（不动用户真在用的浏览器）==="
$SSH "pkill -f 'atlantic-browser --help'; pkill -f 'atlantic-browser.bin --help'; sleep 1; pgrep -af 'atlantic-browser|WPEWebProcess' | cut -c1-120 || echo '(已清空)'"
echo "=== 最上层窗口 ==="
$SSH "su - defaultuser -c 'XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId' 2>&1 | head -2"
