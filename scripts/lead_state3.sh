#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- state:'; cat /run/user/100000/saildroid/com.tencent.mobileqq.json 2>&1; echo; echo '--- launcher log tail:'; tail -6 /home/art/test/sdtool-com.tencent.mobileqq-*.log 2>/dev/null | tail -8; echo '--- procs:'; pgrep -af 'saildroid-supervisor' || echo none"
