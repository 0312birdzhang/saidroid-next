#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
$SSH '. /home/art/env.sh; cd /home/art/test; \
  dalvikvm -cp /home/art/test/ap.dex AssetProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
    /home/art/framework/framework-res.apk /home/art/framework/framework-res.apk \
    > /home/art/test/ap.log 2>&1; echo "rc=$?"'
echo "=== AP 标记 ==="
$SSH "grep -a 'AP\[' /home/art/test/ap.log | head -30"
echo "=== 尾部 ==="
$SSH "grep -av 'packed reloc' /home/art/test/ap.log | tail -20"
