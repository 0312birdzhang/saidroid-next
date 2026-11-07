#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
# 我误触打开的相机，用 SIGTERM 正常关掉（它是我点出来的，不该留给你）
$SSH "pkill -TERM -x jolla-camera; sleep 1; pidof jolla-camera || echo CAMERA_CLOSED" 2>&1
sleep 1
$SSH "python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot pm-final 2>&1" 2>&1
echo "=== 复核关键指标 ==="
$SSH "cat /proc/uptime; free -m | head -3; ls -l /proc/\$(pidof lipstick)/fd 2>/dev/null | grep -o '/dev/input/event[0-9]*' | sort | uniq -c" 2>&1
