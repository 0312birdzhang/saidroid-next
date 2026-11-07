#!/bin/sh
REPO=/media/psf/Home/WorkSpace/saidroid-next
for i in $(seq 1 20); do
  state=$(/bin/sh "$REPO/scripts/devlock.sh" status 2>&1 | head -1)
  case "$state" in *LOCK_FREE*) echo "READY t=$((i*10))s $state"; exit 0;; esac
  case "$state" in *sd-webview*) echo "MINE t=$((i*10))s $state"; exit 0;; esac
  sleep 10
done
echo "STILL_BUSY $(/bin/sh "$REPO/scripts/devlock.sh" status 2>&1 | head -1)"
