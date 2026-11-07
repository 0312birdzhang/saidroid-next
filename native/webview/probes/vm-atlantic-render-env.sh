#!/bin/sh
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-headers"
mkdir -p "$OUT"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15 'echo DEVICE_OK' >/dev/null
/bin/sh "$REPO/native/webview/probes/atlantic-render-env.sh" > "$OUT/atlantic-render-env.txt" 2>&1
echo "WROTE"
