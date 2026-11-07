#!/bin/bash
# P5: sampler on vs off on the same static page, same binary, same env.
set -uo pipefail
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
cd /media/psf/Home/WorkSpace/saidroid-next
status=0
cleanup() {
  python3 scripts/perf/close-owned-vm.py >/dev/null 2>&1
  python3 scripts/perf/restore-baseline-vm.py api29-r78 || status=7
  scripts/devlock.sh release sd-runtime || status=8
}
trap cleanup EXIT
scripts/devlock.sh acquire 600 sd-runtime || { echo "WINDOW_REFUSED reason=lock"; exit 2; }
python3 scripts/perf/close-owned-vm.py || exit 4
sshpass -e ssh -o StrictHostKeyChecking=no root@bonito \
  'ln -sfn /home/art/releases/api29-r79c /home/art/api29-root && readlink /home/art/api29-root' || exit 5
python3 scripts/perf/install-scroll-vm.py r79-probe4 || exit 6
python3 scripts/perf/run-matrix-vm.py r79c --only scroll-gate-perf --only scroll-gate-muted
python3 scripts/perf/check-gate-vm.py build/perf/scroll-gate-muted-r79c build/perf/scroll-gate-perf-r79c
status=$?
echo "GATE_DONE status=$status"
exit $status
