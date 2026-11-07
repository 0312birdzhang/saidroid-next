#!/bin/bash
# 第三次 lipstick 崩溃现场（发生在 r80 手势窗口内）。只取证，不改任何东西。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
echo "=== NOW"
$SSH 'date; cat /proc/sys/kernel/random/boot_id; cut -d" " -f1 /proc/uptime; p=$(pidof lipstick); echo "lipstick_pid=$p"; cut -d" " -f22 /proc/$p/stat'
echo "=== SYSTEMD"
$SSH 'systemctl status lipstick --no-pager 2>&1 | head -20'
echo "=== ANOM_ABEND / SEGV in journal this boot"
$SSH 'journalctl -b --no-pager 2>/dev/null | grep -nE "ANOM_ABEND|sig=11|SEGV|segfault|restart counter" | tail -20'
echo "=== evdevtouch lines"
$SSH 'journalctl -b --no-pager 2>/dev/null | grep -n "evdevtouch" | tail -20'
echo "=== events around the newest lipstick start"
$SSH 'systemctl show lipstick -p ActiveEnterTimestamp -p NRestarts 2>/dev/null'
echo "=== rich-core"
$SSH 'cat /proc/sys/kernel/core_pattern; journalctl -b --no-pager 2>/dev/null | grep -i "rich-core" | tail -5'
echo "=== touch device fds now"
$SSH 'p=$(pidof lipstick); ls -l /proc/$p/fd 2>/dev/null | grep -E "event[0-9]" | sed "s/.*-> //" | sort | uniq -c'
echo "=== dmesg tail"
$SSH 'dmesg | tail -25'
