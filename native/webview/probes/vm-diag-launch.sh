#!/bin/sh
# VM-side wrapper: push + run native/webview/probes/diag1-webproc-launch.sh on the
# device and pull its log back.  The device script takes and releases the shared
# device lock itself, and kills every WPE helper on exit.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8"
SSH="sshpass -e ssh $SSH_OPTS root@192.168.2.15"
SCP="sshpass -e scp $SSH_OPTS"
REPO=/media/psf/Home/WorkSpace/saidroid-next
DEST="$REPO/build/codex-api29/webview-diag"
BIN="${SD_SPIKE_BIN:-/var/tmp/sd-webview-spike/wpe_offscreen_spike}"

echo "== device reachability"
$SSH "true" || { echo DEVICE_UNREACHABLE; exit 1; }

echo "== stage"
$SSH "mkdir -p /home/art/test/webview-spike /home/art/test/webview-diag"
$SCP "$BIN" "root@192.168.2.15:/home/art/test/webview-spike/wpe_offscreen_spike" >/dev/null || { echo SCP_BIN_FAILED; exit 4; }
$SCP "$REPO/native/webview/probes/diag1-webproc-launch.sh" "root@192.168.2.15:/home/art/test/diag1.sh" >/dev/null || { echo SCP_SCRIPT_FAILED; exit 4; }
$SSH "chmod 755 /home/art/test/webview-spike/wpe_offscreen_spike /home/art/test/diag1.sh"

echo "== run diagnostic (bounded by the device script itself)"
$SSH "/home/art/test/diag1.sh" || true

echo "== collect"
$SSH "cat /home/art/test/webview-diag/diag.log"
mkdir -p "$DEST"
$SCP -r "root@192.168.2.15:/home/art/test/webview-diag/." "$DEST/" 2>/dev/null || echo SCP_BACK_FAILED
echo "== evidence: $DEST"
