#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
echo "=== 推送最新探针与桥 ==="
$SCP /tmp/ap/libsdbridge.so root@bonito:/home/art/lib/libsdbridge.so
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
echo "=== 运行 ContextProbe ==="
$SSH '. /home/art/env.sh; cd /home/art/test; dalvikvm -cp /home/art/test/ap.dex ContextProbe /home/art/bio2 /home/art/lib/libsdbridge.so /home/art/framework/framework-res.apk > /home/art/test/ctx.log 2>&1; echo rc=$?'
echo "=== CP 标记 ==="
$SSH "grep -a 'CP\[' /home/art/test/ctx.log | head -40"
echo "=== 尾部 ==="
$SSH "grep -av 'packed reloc' /home/art/test/ctx.log | tail -14 | cut -c1-200"
