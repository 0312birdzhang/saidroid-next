#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
echo "=== CPU 前几名 ==="
$SSH "top -b -n1 | head -18" 2>&1
echo "=== /home/art 相关进程 ==="
$SSH "ps -Ao pid,rss,comm | grep -iE 'saildroid|art|wpe' | grep -v grep" 2>&1
echo "=== 内核 hung / stall 检索 ==="
$SSH "dmesg | grep -iE 'hung|blocked for more than|rcu_sched|stall|watchdog' | tail -12" 2>&1
echo "=== 屏幕状态 ==="
$SSH "gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId 2>&1 | head -3" 2>&1
echo "=== 截图 ==="
$SSH "python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot pm-check 2>&1" 2>&1
