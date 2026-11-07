#!/bin/bash
set -u
IP=${IP:-192.168.3.14}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
S="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@$IP"
echo "=== top cpu consumers (top -b -n1, 前 12)"
$S 'top -b -n 1 -o %CPU 2>/dev/null | head -16' 2>&1
echo "=== 10s 内各进程 CPU 增量 (top 取样两次)"
$S 'top -b -n 2 -d 10 -o %CPU 2>/dev/null | tail -16' 2>&1
echo "=== CPU hotplug 上下文（最近 30 行含 cpu/hotplug 的 dmesg）"
$S 'dmesg | grep -iE "cpu[0-9]|hotplug|APMS|m4m|lmh|qcom,lpass|subsys" | tail -30' 2>&1
echo "=== wdog 前后各一行"
$S 'dmesg | grep -B1 -A1 "wdog_bark" | tail -12' 2>&1
echo "=== 各 cpu 的 online 文件"
$S 'for c in 3 4 5 6 7; do echo "cpu$c online=$(cat /sys/devices/system/cpu/cpu$c/online 2>/dev/null)"; done' 2>&1
echo "=== devfreq/opp 是否报错"
$S 'dmesg | grep -icE "error|fail|timeout"' 2>&1
$S 'dmesg | grep -iE "error|fail|timeout" | tail -15' 2>&1
