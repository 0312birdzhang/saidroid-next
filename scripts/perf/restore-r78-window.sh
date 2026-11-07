#!/bin/bash
# Put the team baseline release back after a measurement window, under the lock.
set -uo pipefail
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
cd /media/psf/Home/WorkSpace/saidroid-next
scripts/devlock.sh acquire 300 sd-runtime || exit 2
python3 scripts/perf/close-owned-vm.py >/dev/null 2>&1
python3 scripts/perf/restore-baseline-vm.py api29-r78
rc=$?
scripts/devlock.sh release sd-runtime
exit $rc
