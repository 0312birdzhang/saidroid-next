#!/bin/sh
set -u
REPO=/media/psf/Home/WorkSpace/saidroid-next
cd "$REPO" || exit 1
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8"
SSH="sshpass -e ssh $SSH_OPTS root@192.168.2.15"
SCP="sshpass -e scp $SSH_OPTS"
DEST="$REPO/build/codex-api29/webview-diag4"
BIN="${SD_SPIKE_BIN:-/var/tmp/sd-webview-spike/wpe_offscreen_spike}"
sh scripts/devlock.sh acquire 20 sd-webview || { echo DEVICE_BUSY; exit 1; }
release() { $SSH "pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null; pkill -9 -f wpe_offscreen_spike 2>/dev/null" >/dev/null 2>&1; sh scripts/devlock.sh release sd-webview; }
trap release EXIT INT TERM
$SCP "$BIN" "root@192.168.2.15:/home/art/test/webview-spike/wpe_offscreen_spike" >/dev/null || { echo SCP_BIN_FAILED; exit 4; }
$SCP "$REPO/native/webview/probes/diag4-eglstubs.sh" "root@192.168.2.15:/home/art/test/diag4.sh" >/dev/null || exit 4
$SSH "chmod 755 /home/art/test/webview-spike/wpe_offscreen_spike /home/art/test/diag4.sh"
$SSH "/home/art/test/diag4.sh" || true
echo "===== diag4.log ====="
$SSH "cat /home/art/test/webview-diag4/diag4.log"
mkdir -p "$DEST"; $SCP -r "root@192.168.2.15:/home/art/test/webview-diag4/." "$DEST/" 2>/dev/null || echo SCP_BACK_FAILED
echo "== evidence: $DEST"
