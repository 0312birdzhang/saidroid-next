#!/bin/bash
# 重启后复核四项：event1 fd / hwservicemanager 空转 / cpu_online+热插拔 / wdog_bark
set -u
IP=${IP:-192.168.3.14}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
S="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@$IP"
out=/tmp/post_reboot.txt
{
echo "=== when: $(date -Is)"
echo "=== boot: $($S 'cat /proc/sys/kernel/random/boot_id; cut -d" " -f1 /proc/uptime' 2>&1 | tr "\n" " ")"
echo "=== lipstick"
$S 'pid=$(pidof lipstick); echo "pid=$pid"; cut -d" " -f22 /proc/$pid/stat; echo "--- fds on /dev/input ---"; for f in /proc/$pid/fd/*; do t=$(readlink $f 2>/dev/null); case "$t" in *input*) echo "$(basename $f) -> $t";; esac; done' 2>&1
echo "=== hwservicemanager"
$S 'pid=$(pidof hwservicemanager); echo "pid=$pid"; cut -d" " -f1 /proc/uptime; awk "{print \"utime=\"\$14\" stime=\"\$15\" starttime=\"\$22}" /proc/$pid/stat; sleep 30; cut -d" " -f1 /proc/uptime; awk "{print \"utime=\"\$14\" stime=\"\$15\" starttime=\"\$22}" /proc/$pid/stat' 2>&1
echo "=== cpu"
$S 'echo "online: $(cat /sys/devices/system/cpu/online)"; echo "offline: $(cat /sys/devices/system/cpu/offline 2>/dev/null)"; echo "present: $(cat /sys/devices/system/cpu/present)"; echo "--- secondary booted ---"; dmesg 2>/dev/null | grep -c "Booted secondary processor"; dmesg 2>/dev/null | grep "Booted secondary processor" | awk "{print \$NF}" | sort | uniq -c' 2>&1
echo "=== wdog"
$S 'dmesg 2>/dev/null | grep -c "wdog_bark"; dmesg 2>/dev/null | grep "wdog_bark" | tail -3' 2>&1
echo "=== load/mem"
$S 'uptime; free -m | head -3' 2>&1
echo "=== thermal"
$S 'for z in /sys/class/thermal/thermal_zone*; do printf "%s %s\n" "$(cat $z/type 2>/dev/null)" "$(cat $z/temp 2>/dev/null)"; done | head -12' 2>&1
} > $out 2>&1
cat $out
