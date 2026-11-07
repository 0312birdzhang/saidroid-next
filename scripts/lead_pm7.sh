#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
echo "=== lipstick 打开的每个 event 设备及重复次数 ==="
$SSH "ls -l /proc/46884/fd 2>/dev/null | grep -o '/dev/input/event[0-9]*' | sort | uniq -c | sort -nr" 2>&1
echo "=== 每个 eventN 对应的设备名 ==="
$SSH "grep -B3 -A1 'event' /proc/bus/input/devices 2>/dev/null | grep -E 'Name=|Handlers=' | head -24" 2>&1
echo "=== 触摸设备（有 ABS_MT 的） ==="
$SSH "for f in /sys/class/input/event*/device/name; do n=\$(cat \$f 2>/dev/null); echo \"\${f%/device/name}: \$n\"; done" 2>&1
echo "=== 当前屏幕 ==="
$SSH "python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot pm-now 2>&1" 2>&1
