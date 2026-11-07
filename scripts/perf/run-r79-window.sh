#!/bin/bash
# One self-contained r79 measurement window: take the device lock, deploy the
# direct-copy component, run the matrix, put the team baseline (r78) back, and
# release the lock even if anything failed.
#
#   prlctl exec "MeeGo Build" /media/psf/Home/WorkSpace/saidroid-next/scripts/perf/run-r79-window.sh
#
# Run inside the MeeGo Build VM. Nothing here is destructive outside /home/art:
# the release directory stays on disk, only the api29-root symlink moves back.
set -uo pipefail
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
cd /media/psf/Home/WorkSpace/saidroid-next

status=0
cleanup() {
  echo "=== cleanup: restore r78 and release the lock"
  python3 scripts/perf/close-owned-vm.py >/dev/null 2>&1
  python3 scripts/perf/restore-baseline-vm.py api29-20261026-r78 || status=7
  scripts/devlock.sh release sd-runtime || status=8
}
trap cleanup EXIT

echo "=== acquire"
scripts/devlock.sh acquire 900 sd-runtime || { echo "WINDOW_REFUSED reason=lock"; exit 2; }
scripts/devlock.sh status

scripts/perf/window-r79.sh
status=$?
echo "=== window status=$status"
exit $status
