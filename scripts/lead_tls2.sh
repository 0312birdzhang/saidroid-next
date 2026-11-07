#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "L=/home/art/data/logs/com.tencent.mobileqq/20261027T050101-47506.log; echo LOG=\$L; wc -l \$L; echo '--- SSL/cert:'; grep -n -i 'sslhandshake\|certificate\|turingfd\|-329' \$L | head -20; echo '--- 尾部 30 行:'; tail -30 \$L"
