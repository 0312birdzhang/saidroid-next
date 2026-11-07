#!/bin/bash
# Lead 只读探针：不拿设备锁，只查状态，不做任何写操作。
# 在 VM 里跑：prlctl exec "MeeGo Build" "/bin/bash <repo>/scripts/lead_probe_device.sh"
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"

echo "=== PERF FILES ==="
$SSH "ls -lt /home/art/test/ /var/tmp/ 2>/dev/null | grep -i perf | head -10" 2>&1
echo "=== QQ LOGS ==="
$SSH "ls -lt /home/art/data/logs/com.tencent.mobileqq/ 2>/dev/null | head -5" 2>&1
echo "=== SAILDROID PROCS ==="
$SSH "ps -eo pid,etimes,comm | grep -Ei 'art|saildroid|qq' | grep -v grep | head -20" 2>&1
echo "=== TOPMOST ==="
$SSH "su defaultuser -s /bin/sh -c 'XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId'" 2>&1
echo "=== MEM ==="
$SSH "free -m | head -2" 2>&1
echo "=== DISK ==="
$SSH "df -h /home /var/tmp 2>/dev/null | tail -3" 2>&1
