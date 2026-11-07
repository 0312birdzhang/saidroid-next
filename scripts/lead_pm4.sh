#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
echo "=== 按累计 CPU 时间排前 12（utime+stime） ==="
$SSH "for p in /proc/[0-9]*; do pid=\${p#/proc/}; [ -r \$p/stat ] || continue; awk -v pid=\$pid '{print pid, \$14+\$15, \$2}' \$p/stat 2>/dev/null; done | sort -k2 -nr | head -12" 2>&1
echo "=== 这些 pid 的命令行 ==="
$SSH "for pid in \$(for p in /proc/[0-9]*; do pid=\${p#/proc/}; [ -r \$p/stat ] || continue; awk -v pid=\$pid '{print pid, \$14+\$15}' \$p/stat 2>/dev/null; done | sort -k2 -nr | head -8 | cut -d' ' -f1); do printf '%s ' \$pid; tr '\0' ' ' < /proc/\$pid/cmdline 2>/dev/null | cut -c1-90; echo; done" 2>&1
echo "=== 僵尸/异常状态统计 ==="
$SSH "for p in /proc/[0-9]*; do [ -r \$p/stat ] || continue; awk '{print \$3}' \$p/stat; done | sort | uniq -c" 2>&1
echo "=== 当前前台窗口进程 ==="
$SSH "su defaultuser -c 'XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId'" 2>&1 | tail -2
