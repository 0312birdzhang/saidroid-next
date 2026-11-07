#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
B=/tmp/art-build/bionic_translation/builddir
$SCP $B/libc_bio.so.0 root@bonito:/home/art/lib/libc_bio.so.0
$SCP $B/libc_bio.so.0 root@bonito:/home/art/bio2/libc_bio.so.0
$SCP /tmp/ap/libsdbridge.so root@bonito:/home/art/lib/libsdbridge.so
echo "=== 设备上 ldd -r 检查 ==="
$SSH "LD_LIBRARY_PATH=/home/art/lib ldd -r /home/art/lib/libc_bio.so.0 2>&1 | grep -i 'not found\|undefined' | head -5; echo '(空=全解析)'"
echo "=== 跑探针 ==="
$SSH '. /home/art/env.sh; cd /home/art/test; dalvikvm -cp /home/art/test/ap.dex AssetProbe /home/art/bio2 /home/art/lib/libsdbridge.so /home/art/framework/framework-res.apk > /home/art/test/ap.log 2>&1; echo rc=$?'
echo "=== SDBRIDGE 预载 ==="
$SSH "grep -a 'glibc dlopen' /home/art/test/ap.log | head -5"
echo "=== AP 标记 ==="
$SSH "grep -a 'AP\[' /home/art/test/ap.log | head -20"
