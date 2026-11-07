#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
B=/tmp/art-build/bionic_translation/builddir
ls -l $B/libdl_bio.so.0.0.1 $B/libc_bio.so.0
$SCP $B/libdl_bio.so.0.0.1 root@bonito:/home/art/lib/libdl_bio.so.0.0.1
$SCP $B/libdl_bio.so.0.0.1 root@bonito:/home/art/bio2/libdl_bio.so.0.0.1
$SCP $B/libc_bio.so.0 root@bonito:/home/art/lib/libc_bio.so.0
$SCP $B/libc_bio.so.0 root@bonito:/home/art/bio2/libc_bio.so.0
$SSH "cp -f /home/art/lib/libdl_bio.so.0.0.1 /home/art/lib/libdl_bio.so.0; cp -f /home/art/bio2/libdl_bio.so.0.0.1 /home/art/bio2/libdl_bio.so.0; ls -l /home/art/lib/libdl_bio.so.0 /home/art/lib/libc_bio.so.0"
$SCP /tmp/ap/libsdbridge.so root@bonito:/home/art/lib/libsdbridge.so
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SSH '. /home/art/env.sh; cd /home/art/test
      dalvikvm -cp /home/art/test/ap.dex QQProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
        /home/art/realapps/qq.apk /home/art/realapps/qq-libs > /home/art/test/qq.log 2>&1; echo rc=$?'
echo "=== 关键标记 ==="
$SSH "grep -a '预热\|预载 lib\|QQ Application\|baseContext\|UnsatisfiedLink\|Caused by' /home/art/test/qq.log | head -12"
