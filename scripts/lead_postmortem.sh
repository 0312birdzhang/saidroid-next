#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
echo "=== 可达性 ==="
$SSH "date; uptime; cat /proc/loadavg" 2>&1 || echo SSH_FAIL
echo "=== 内存 ==="
$SSH "free -m; echo ---; cat /proc/meminfo | grep -E 'MemAvailable|SwapFree|Dirty'" 2>&1
echo "=== 磁盘 ==="
$SSH "df -h / /home /tmp /var/tmp 2>/dev/null | head -8" 2>&1
echo "=== lipstick/关键进程 ==="
$SSH "pidof lipstick; pidof lipstick-security-ui; pidof sailfish-home; echo ---; ps -Ao pid,rss,pcpu,comm --sort=-rss | head -14" 2>&1
echo "=== SailDroid 残留 ==="
$SSH "ps -Ao pid,rss,args | grep -iE 'saildroid|WPEWeb|art' | grep -v grep | head -12" 2>&1
echo "=== OOM / 内核告警 ==="
$SSH "dmesg | tail -40" 2>&1
echo "=== journal 最近 25 行 ==="
$SSH "journalctl --no-pager -o short-iso -n 25" 2>&1
