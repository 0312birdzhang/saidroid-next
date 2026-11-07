#!/bin/bash
set -u
REPO=/media/psf/Home/WorkSpace/saidroid-next
cd "$REPO" || exit 1
/bin/sh scripts/devlock.sh acquire 480 sd-webview || { echo LOCK_ACQUIRE_FAILED; exit 2; }
trap '/bin/sh "'"$REPO"'/scripts/devlock.sh" release sd-webview' EXIT
/bin/bash native/webview/tools/vm-drawdiag-3step.sh "${1:-whiteboard3}"
