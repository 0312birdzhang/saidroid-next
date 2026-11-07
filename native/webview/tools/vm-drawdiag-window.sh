#!/bin/bash
# One-shot window: take the device lock as sd-webview, run the whiteboard diagnosis,
# always release. Hard cap: the run script kills itself after 9 minutes.
set -u
REPO=/media/psf/Home/WorkSpace/saidroid-next
cd "$REPO" || exit 1
RUN=${1:-whiteboard1}
/bin/sh scripts/devlock.sh acquire 900 sd-webview || { echo LOCK_ACQUIRE_FAILED; exit 2; }
trap '/bin/sh "'"$REPO"'/scripts/devlock.sh" release sd-webview; echo "LOCK_RELEASED"' EXIT
/bin/bash native/webview/tools/vm-run-drawdiag.sh "$RUN"
