#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
echo "=== 时间/启动 ==="
$SSH "date; cat /proc/uptime; cat /proc/sys/kernel/random/boot_id; echo ---; uptime" 2>&1
echo "=== 内存 ==="
$SSH "free -m" 2>&1
echo "=== 磁盘 ==="
$SSH "df -h / /home 2>/dev/null; echo ---; du -sh /home/art 2>/dev/null; ls -1 /home/art/releases 2>/dev/null" 2>&1
echo "=== 关键进程 ==="
$SSH "pidof lipstick; pidof lipstick-security-ui; echo ---; ps -Ao pid,rss,pcpu,args --sort=-rss | head -8" 2>&1
echo "=== OOM/abend 检索（dmesg 全量） ==="
$SSH "dmesg | grep -iE 'oom|killed process|out of memory|lowmemory|ANOM_ABEND|watchdog' | tail -25" 2>&1
echo "=== journal 起点（=最后一次重启时间）与崩溃记录 ==="
$SSH "journalctl --no-pager -o short-iso | head -3; echo ---; journalctl --no-pager -o short-iso | grep -E 'ANOM_ABEND|code=dumped|Failed with result|Scheduled restart' | tail -12" 2>&1
echo "=== 历史启动次数（wtmp） ==="
$SSH "last -x reboot 2>/dev/null | head -6; echo ---; last -x shutdown 2>/dev/null | head -4" 2>&1
