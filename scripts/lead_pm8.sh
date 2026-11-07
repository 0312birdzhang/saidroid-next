#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
# 从底部上滑回 Home（关掉被误触打开的相机）
$SSH "/home/art/bin/sdinput swipe 540 2100 540 700 300 30" 2>&1
sleep 2
$SSH "python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot pm-home 2>&1" 2>&1
echo "=== 误触验证：哪些进程在跑 ==="
$SSH "pidof jolla-camera; pidof camera-ui; pidof jolla-gallery" 2>&1
echo "=== hwservicemanager 是否为循环重启 ==="
$SSH "journalctl --no-pager -o short-iso -S '-20 min' | grep -icE 'hwservicemanager|strongbox|keymaster'" 2>&1
$SSH "cat /proc/6434/stat 2>/dev/null | awk '{print \"hwsm_state=\"\$3, \"utime=\"\$14, \"stime=\"\$15, \"starttime=\"\$22}'" 2>&1
$SSH "cat /proc/uptime" 2>&1
