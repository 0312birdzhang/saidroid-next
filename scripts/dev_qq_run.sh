#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SSH '. /home/art/env.sh; cd /home/art/test; \
  dalvikvm -cp /home/art/test/ap.dex QQProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
    /home/art/realapps/qq.apk /home/art/realapps/qq-libs \
    > /home/art/test/qq.log 2>&1; echo rc=$?'
echo "=== QP 标记 ==="
$SSH "grep -a 'QP\[' /home/art/test/qq.log | head -30"
echo "=== 尾部 ==="
$SSH "grep -av 'packed reloc' /home/art/test/qq.log | tail -12 | cut -c1-200"
