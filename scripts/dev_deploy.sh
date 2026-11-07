#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
B=/tmp/art-build/bionic_translation/builddir
NEW=$B/libc_bio.so.0
echo "=== 待部署版本 ==="
ls -l $NEW $B/libdl_bio.so.0.0.1 /tmp/ap/libsdbridge.so /tmp/ap/ap.dex
echo "=== 推送到设备 ==="
$SCP $NEW root@bonito:/home/art/lib/libc_bio.so.0 && echo "  libc_bio -> lib OK"
$SCP $NEW root@bonito:/home/art/bio2/libc_bio.so.0 && echo "  libc_bio -> bio2 OK"
$SCP $B/libdl_bio.so.0.0.1 root@bonito:/home/art/lib/libdl_bio.so.0.0.1 && echo "  libdl_bio.0.0.1 -> lib OK"
$SCP $B/libdl_bio.so.0.0.1 root@bonito:/home/art/bio2/libdl_bio.so.0.0.1 && echo "  libdl_bio.0.0.1 -> bio2 OK"
$SCP /tmp/ap/libsdbridge.so root@bonito:/home/art/lib/libsdbridge.so && echo "  libsdbridge OK"
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex && echo "  ap.dex OK"
echo "=== 修正 libdl_bio.so.0 ==="
$SSH "cp -f /home/art/lib/libdl_bio.so.0.0.1 /home/art/lib/libdl_bio.so.0;
      cp -f /home/art/bio2/libdl_bio.so.0.0.1 /home/art/bio2/libdl_bio.so.0;
      ls -l /home/art/lib/libc_bio.so.0 /home/art/bio2/libc_bio.so.0"
echo "=== 校验新属性表是否到位 ==="
$SSH "strings /home/art/lib/libc_bio.so.0 | grep -c 'ro.product.cpu.abilist32'"
