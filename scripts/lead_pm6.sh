#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
echo "=== 背光与显示状态 ==="
$SSH "cat /sys/class/leds/lcd-backlight/brightness 2>/dev/null; cat /sys/class/backlight/*/brightness 2>/dev/null; echo ---; gdbus call --system --dest com.nokia.mce --object-path /com/nokia/mce/request --method com.nokia.mce.request.get_display_status 2>&1 | head -2" 2>&1
echo "=== tklock / 屏幕锁定 ==="
$SSH "gdbus call --system --dest com.nokia.mce --object-path /com/nokia/mce/request --method com.nokia.mce.request.get_device_lock_status 2>&1 | head -2" 2>&1
echo "=== 唤醒尝试：注入一次轻点 ==="
$SSH "/home/art/bin/sdinput tap 540 1000 60" 2>&1
sleep 2
$SSH "cat /sys/class/leds/lcd-backlight/brightness 2>/dev/null; python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot pm-wake 2>&1" 2>&1
echo "=== lipstick 是否在画（最近 journal） ==="
$SSH "journalctl --no-pager -o short-iso -S '-3 min' | tail -12" 2>&1
