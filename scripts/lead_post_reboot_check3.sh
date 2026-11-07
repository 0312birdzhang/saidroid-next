#!/bin/bash
set -u
IP=${IP:-192.168.3.14}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
S="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@$IP"
echo "=== hwservicemanager 内核栈/wchan/syscall 采样"
$S 'p=$(pidof hwservicemanager); echo pid=$p; for i in 1 2 3 4 5; do echo "-- $i"; cat /proc/$p/wchan 2>/dev/null; echo; cat /proc/$p/syscall 2>/dev/null; cat /proc/$p/stack 2>/dev/null | head -6; sleep 1; done' 2>&1
echo "=== 它的线程数/线程名"
$S 'p=$(pidof hwservicemanager); ls /proc/$p/task | wc -l; for t in /proc/$p/task/*; do echo "$(basename $t) $(cat $t/comm) $(cat $t/wchan 2>/dev/null)"; done | head -20' 2>&1
echo "=== 自开机以来各进程 CPU 排行（/proc 累计 jiffies）"
$S 'for p in /proc/[0-9]*; do pid=${p#/proc/}; [ -r $p/stat ] || continue; c=$(cut -d" " -f14,15 $p/stat | tr -d "\n"); u=$(echo $c | cut -d, -f1); s=$(echo $c | cut -d, -f2); echo "$((u+s)) $pid $(cut -d" " -f2 $p/stat)"; done | sort -rn | head -12' 2>&1
echo "=== charging 相关 sysfs"
$S 'for f in /sys/class/power_supply/*/status /sys/class/power_supply/*/capacity /sys/class/power_supply/*/online; do printf "%s = %s\n" "$f" "$(cat $f 2>/dev/null)"; done' 2>&1
