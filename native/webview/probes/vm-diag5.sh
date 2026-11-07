#!/bin/sh
# VM driver for diag5: take the device lock via scripts/devlock.sh, push the
# spike + diag5 to the device, run the HYBRIS_EGLPLATFORM=wayland matrix, pull
# all evidence back, always release the lock.
#
# Usage (in the VM):  /bin/sh native/webview/probes/vm-diag5.sh [lock_seconds]
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
DEST="$REPO/build/codex-api29/webview-diag5"
REMOTE=/home/art/test/webview-diag5
BIN=/var/tmp/sd-webview-spike/wpe_offscreen_spike
LOCK_SECS=${1:-240}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8"

mkdir -p "$DEST"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 'echo DEVICE_OK' || { echo DEVICE_UNREACHABLE; exit 3; }

echo "== acquire device lock"
/bin/sh "$REPO/scripts/devlock.sh" acquire "$LOCK_SECS" sd-webview || { echo LOCK_FAILED; exit 3; }
release() { /bin/sh "$REPO/scripts/devlock.sh" release sd-webview || true; }
trap release EXIT INT TERM

[ -f "$BIN" ] || { echo "MISSING_BINARY $BIN"; exit 2; }

echo "== kill leftovers before start"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null; pkill -9 -f wpe_offscreen_spike 2>/dev/null; sleep 1; echo LEFTOVER=\$(pgrep -cf 'wpe-webkit-2.0' || true)" || true

echo "== stage"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "rm -rf '$REMOTE' && mkdir -p '$REMOTE/out'" || true
sshpass -e scp $SSH_OPTS "$BIN" "root@192.168.2.15:$REMOTE/wpe_offscreen_spike"
sshpass -e scp $SSH_OPTS "$REPO/native/webview/probes/diag5-eglplatform.sh" "root@192.168.2.15:$REMOTE/diag5.sh"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "chmod 755 '$REMOTE/diag5.sh' '$REMOTE/wpe_offscreen_spike'"

echo "== run diag5 (env matrix)"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "SD_SPIKE_OUT='$REMOTE/out' '/bin/sh' '$REMOTE/diag5.sh'" 2>&1 | tee "$DEST/diag5.log" || true

echo "== pull evidence"
sshpass -e scp -r $SSH_OPTS "root@192.168.2.15:$REMOTE/out/." "$DEST/" || echo SCP_BACK_FAILED
ls -l "$DEST" | head -20

echo "== aftermath"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "pgrep -a -f 'wpe-webkit-2.0' | head -5; echo ---; dmesg | tail -12" || true

echo "== evidence in $DEST"
