#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "/home/art/bin/saildroid-open --package com.tencent.mobileqq --close 2>&1 | tail -3; sleep 2; pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null; echo '--- 残留进程:'; pgrep -af 'saildroid-supervisor|SdRuntime|wpe-webkit|WPEWeb|spike' 2>/dev/null || echo none"
