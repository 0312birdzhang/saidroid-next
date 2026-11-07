#!/bin/sh
# VM-side driver: run the read-only renderer-host header dump against the device.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-headers"
mkdir -p "$OUT"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15 'echo DEVICE_OK; uname -r' || { echo DEVICE_UNREACHABLE; exit 3; }
/bin/sh "$REPO/native/webview/probes/dump-renderer-host-headers.sh" > "$OUT/renderer-host-headers.txt" 2>&1
echo "WROTE $OUT/renderer-host-headers.txt"
wc -l "$OUT/renderer-host-headers.txt"
grep -c . "$OUT/renderer-host-headers.txt" || true
