#!/bin/sh
# Push + run diag7 (three untested libhybris eglplatform backends) under the shared
# device lock, then pull the evidence back. Hard cap 75 s: the device script itself
# bounds each variant to 13 s; this wrapper kills the ssh command if anything hangs
# and always kills the SPIKE + WPE helpers and releases the lock.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-diag7"
REMOTE=/home/art/test/webview-diag7
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=8"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"

sshpass -e ssh $SSH_OPTS root@192.168.2.15 'echo DEVICE_OK' >/dev/null
ST=$(sshpass -e ssh $SSH_OPTS root@192.168.2.15 'cat /home/art/test/.device-lock/owner 2>/dev/null || echo LOCK_FREE')
echo "LOCK_STATE=$ST"
case "$ST" in
    LOCK_FREE) /bin/sh "$REPO/scripts/devlock.sh" acquire 300 sd-webview || exit 3 ;;
    *sd-webview*) : ;;
    *) echo "LOCK_NOT_MINE owner=$ST"; exit 3 ;;
esac
trap '
  sshpass -e ssh $SSH_OPTS root@192.168.2.15 "pkill -9 -f wpe_offscreen_spike; pkill -9 -f wpe-webkit-2.0" >/dev/null 2>&1 || true
  /bin/sh "$REPO/scripts/devlock.sh" release sd-webview >/dev/null 2>&1 || true
' EXIT INT TERM

mkdir -p "$OUT"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "rm -rf '$REMOTE/out'; mkdir -p '$REMOTE/out'" || true
sshpass -e scp $SSH_OPTS \
    "$REPO/native/webview/probes/diag7-eglplatforms.sh" root@192.168.2.15:"$REMOTE/diag7.sh" >/dev/null
sshpass -e scp $SSH_OPTS \
    /var/tmp/sd-webview-spike/wpe_offscreen_spike root@192.168.2.15:"$REMOTE/wpe_offscreen_spike" >/dev/null
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "chmod +x '$REMOTE/diag7.sh' '$REMOTE/wpe_offscreen_spike'" >/dev/null

sshpass -e ssh $SSH_OPTS root@192.168.2.15 "sh '$REMOTE/diag7.sh'" > "$OUT/diag7.log" 2>&1 &
SSH_PID=$!
( sleep 75; kill -9 "$SSH_PID" 2>/dev/null
  sshpass -e ssh $SSH_OPTS root@192.168.2.15 "pkill -9 -f wpe_offscreen_spike; pkill -9 -f wpe-webkit-2.0" >/dev/null 2>&1 || true ) &
GUARD=$!
wait "$SSH_PID" 2>/dev/null || true
kill -9 "$GUARD" 2>/dev/null || true

sshpass -e scp $SSH_OPTS -r root@192.168.2.15:"$REMOTE/out/*" "$OUT/" >/dev/null 2>&1 || true
echo "PULLED $(ls -1 "$OUT" 2>/dev/null | tr '\n' ' ')"
grep -E 'VARIANT=|FRAMES=|spike_result|Assertion|Fatal|summary' "$OUT/diag7.log" 2>/dev/null | head -40
