#!/bin/sh
# VM-side wrapper for native/webview/probes/diag2-webproc.sh.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8"
SSH="sshpass -e ssh $SSH_OPTS root@192.168.2.15"
SCP="sshpass -e scp $SSH_OPTS"
REPO=/media/psf/Home/WorkSpace/saidroid-next
DEST="$REPO/build/codex-api29/webview-diag2"
BIN="${SD_SPIKE_BIN:-/var/tmp/sd-webview-spike/wpe_offscreen_spike}"

$SSH "true" || { echo DEVICE_UNREACHABLE; exit 1; }
$SSH "mkdir -p /home/art/test/webview-spike"
$SCP "$BIN" "root@192.168.2.15:/home/art/test/webview-spike/wpe_offscreen_spike" >/dev/null || { echo SCP_BIN_FAILED; exit 4; }
$SCP "$REPO/native/webview/probes/diag2-webproc.sh" "root@192.168.2.15:/home/art/test/diag2.sh" >/dev/null || { echo SCP_SCRIPT_FAILED; exit 4; }
$SSH "chmod 755 /home/art/test/webview-spike/wpe_offscreen_spike /home/art/test/diag2.sh"
$SSH "/home/art/test/diag2.sh" || true
echo "===== diag2.log ====="
$SSH "cat /home/art/test/webview-diag2/diag2.log"
mkdir -p "$DEST"
$SCP -r "root@192.168.2.15:/home/art/test/webview-diag2/." "$DEST/" 2>/dev/null || echo SCP_BACK_FAILED
echo "== evidence: $DEST"
