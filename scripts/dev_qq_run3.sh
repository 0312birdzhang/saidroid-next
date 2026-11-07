#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SSH "mkdir -p /home/art/storage/sdcard0 /home/art/data/qq/odex; chmod -R 777 /home/art/storage /home/art/data/qq"
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SSH '. /home/art/env.sh; cd /home/art/test
      dalvikvm -cp /home/art/test/ap.dex QQProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
        /home/art/realapps/qq.apk /home/art/realapps/qq-libs > /home/art/test/qq.log 2>&1
      echo rc=$?'
echo "=== QP 标记 ==="
$SSH "grep -a 'QP\[' /home/art/test/qq.log | head -32"
echo "=== 异常/尾部 ==="
$SSH "grep -a 'Caused by\|Exception\|Error' /home/art/test/qq.log | grep -av 'packed reloc' | head -10"
