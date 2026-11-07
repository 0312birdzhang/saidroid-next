#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
R=/media/psf/Home/WorkSpace/saidroid-next
echo "=== 进程 ==="
$SSH "ps -o pid,stat,comm,args -p 40800 2>/dev/null | cut -c1-100; pgrep -af 'atlantic-browser|WPEWebProcess' | cut -c1-100; echo END"
echo "=== 最上层 ==="
$SSH "su - defaultuser -c 'XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId' 2>&1 | head -2"
echo "=== 截图 ==="
bash $R/scripts/sd.sh shot lead-after-clean 2>&1 | tail -1
