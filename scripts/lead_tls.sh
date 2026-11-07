#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "L=\$(ls -t /home/art/data/logs/com.tencent.mobileqq/*.log | head -1); echo LOG=\$L; echo '--- SSL/TLS 相关:'; grep -n -i 'ssl\|cert\|turing\|wolf' \$L | head -40; echo '--- 退出前 25 行:'; tail -25 \$L"
