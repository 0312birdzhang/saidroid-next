#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
R=/media/psf/Home/WorkSpace/saidroid-next
echo "=== SailDroid 进程 ==="
$SSH "pgrep -af 'saildroid|org.saildroid' | sed 's/ \{2,\}/ /g' | cut -c1-110"
echo "=== QQ 运行记录 ==="
$SSH "python3 /home/art/bin/sdtool.py status 2>/dev/null | head -4"
echo "=== 最上层窗口 ==="
$SSH "su - defaultuser -c 'XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId' 2>&1 | head -2"
echo "=== 再截一张（隔 3 秒）==="
sleep 3
bash $R/scripts/sd.sh shot lead-recover-1 2>&1 | tail -1
