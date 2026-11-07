#!/bin/sh
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-headers"
mkdir -p "$OUT"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15 'echo DEVICE_OK' || { echo DEVICE_UNREACHABLE; exit 3; }
/bin/sh "$REPO/native/webview/probes/find-backend.sh" > "$OUT/find-backend.txt" 2>&1
echo "WROTE $OUT/find-backend.txt"
