#!/bin/bash
# 在 VM 里编译 wolfssl-error 并在手机上跑（只读，不动 ART 实例）。
#   scripts/tls/vm-build-run.sh [-329]
set -u
REPO=/media/psf/Home/WorkSpace/saidroid-next
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=8"
OUT=/tmp/wolfssl-error
gcc -O1 -o "$OUT" "$REPO/scripts/tls/wolfssl-error.c" -ldl || { echo BUILD_FAIL; exit 1; }
echo "BUILD_OK $(stat -c %s "$OUT") bytes"
$SCP -q "$OUT" root@bonito:/home/art/test/wolfssl-error || { echo PUSH_FAIL; exit 1; }
$SSH "/home/art/test/wolfssl-error $* 2>&1 | head -50"
