#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "S=/opt/wpe-sfos/libexec/atlantic/runtime-common.sh; echo '--- 160-200:'; sed -n '160,200p' \$S; echo '--- 830,870:'; sed -n '830,870p' \$S; echo '--- 285,325:'; sed -n '285,325p' \$S"
