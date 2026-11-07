#!/bin/sh
# Runs survey-atlantic.sh on the device under the shared device lock and pulls the
# evidence back into the repo. Refuses to start if the lock is not ours.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-survey"
REMOTE=/home/art/test/webview-survey
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=8"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"

if [ -d /home/art/test/.device-lock ]; then :; fi
sshpass -e ssh $SSH_OPTS root@192.168.2.15 'echo DEVICE_OK' >/dev/null

ST=$(sshpass -e ssh $SSH_OPTS root@192.168.2.15 'cat /home/art/test/.device-lock/owner 2>/dev/null || echo LOCK_FREE')
echo "LOCK_STATE=$ST"
case "$ST" in
    LOCK_FREE)
        # Nobody owns the device: take it ourselves so Atlantic cannot collide with
        # a perf run, and give it back in the trap below.
        /bin/sh "$REPO/scripts/devlock.sh" acquire 300 sd-webview || exit 3
        OWNED=1
        ;;
    *sd-webview*) OWNED=0 ;;
    *) echo "LOCK_NOT_MINE (owner=$ST) -- ask Lead for the device window first"; exit 3 ;;
esac
trap '/bin/sh "$REPO/scripts/devlock.sh" release sd-webview >/dev/null 2>&1 || true' EXIT INT TERM
mkdir -p "$OUT"
sshpass -e ssh $SSH_OPTS root@192.168.2.15 "rm -rf '$REMOTE'; mkdir -p '$REMOTE'" || true
sshpass -e scp $SSH_OPTS /media/psf/Home/WorkSpace/saidroid-next/native/webview/probes/survey-atlantic.sh \
    root@192.168.2.15:/home/art/test/survey-atlantic.sh >/dev/null

# Hard cap: the survey itself is bounded (20 s WebProcess wait + 1 s teardown);
# `timeout` does not exist on the device, so the wrapper enforces the cap by
# killing the whole ssh command after 75 s.
sshpass -e ssh $SSH_OPTS root@192.168.2.15 'chmod +x /home/art/test/survey-atlantic.sh; /home/art/test/survey-atlantic.sh' \
    > "$OUT/survey.log" 2>&1 &
SSH_PID=$!
( sleep 75; kill -9 "$SSH_PID" 2>/dev/null; sshpass -e ssh $SSH_OPTS root@192.168.2.15 \
    "pkill -9 -f atlantic-browser; pkill -9 -f wpe-webkit-2.0" 2>/dev/null ) &
GUARD=$!
wait "$SSH_PID" 2>/dev/null || true
kill -9 "$GUARD" 2>/dev/null || true

sshpass -e scp $SSH_OPTS -r root@192.168.2.15:"$REMOTE/*" "$OUT/" >/dev/null 2>&1 || true
echo "PULLED $(ls -1 "$OUT" | tr '\n' ' ')"
echo "---- key lines ----"
grep -E 'LOCK_STATE|ATLANTIC=|LIPSTICK_|WPEWEBPROCESS_PID|CLASSIFY\||ATLANTIC_LEFT|DONE out=' "$OUT/survey.log" 2>/dev/null
echo "---- wlegl scan hits ----"
grep -v '^##' "$OUT/wlegl-scan.txt" 2>/dev/null | head -10
echo "---- full log ----"
sed -n '1,120p' "$OUT/survey.log" 2>/dev/null
