#!/bin/sh
# Poll the device lock for N seconds (bounded), print the final state.
REPO=/media/psf/Home/WorkSpace/saidroid-next
for i in $(seq 1 12); do
  state=$(/bin/sh "$REPO/scripts/devlock.sh" status 2>&1 | head -1)
  echo "t=$((i*10))s $state"
  case "$state" in *LOCK_FREE*|*sd-webview*) echo "READY"; exit 0;; esac
  sleep 10
done
echo "STILL_BUSY"
