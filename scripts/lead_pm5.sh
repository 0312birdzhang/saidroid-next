#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
echo "=== 遗留的 sdinput 虚拟设备 ==="
$SSH "grep -c 'Name=\"sdinput\"' /proc/bus/input/devices; grep -A2 'Name=\"sdinput\"' /proc/bus/input/devices | head -12" 2>&1
echo "=== lipstick 打开的事件设备 ==="
$SSH "ls -l /proc/46884/fd 2>/dev/null | grep -c event; ls -l /proc/46884/fd 2>/dev/null | grep event | head -6" 2>&1
echo "=== 是否有进程还占着 /dev/uinput ==="
$SSH "fuser -v /dev/uinput 2>&1 | head -6; ls -l /dev/uinput" 2>&1
echo "=== 试一次注入：点屏幕中部，看画面是否变化 ==="
$SSH "sha256sum /home/defaultuser/Downloads/SailDroid-Screenshots/pm-check.png" 2>&1
$SSH "/home/art/bin/sdinput tap 540 1200 80" 2>&1
sleep 2
$SSH "python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot pm-tap 2>&1" 2>&1
