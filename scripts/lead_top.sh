#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "=== 最上层窗口 pid ==="
$SSH "su - defaultuser -c 'XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId' 2>/dev/null || echo QUERY_FAIL"
echo "=== 相关进程 ==="
$SSH "pgrep -af 'saildroid-supervisor|org.saildroid.manager|dalvikvm' | sed 's/ \{2,\}/ /g' | cut -c1-120"
