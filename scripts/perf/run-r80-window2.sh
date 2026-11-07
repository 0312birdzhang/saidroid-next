#!/bin/bash
# r80 second window: the gesture steps only, now that sdinput reports proven writes.
set -uo pipefail
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
cd /media/psf/Home/WorkSpace/saidroid-next
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
EVID=build/evidence/r80
mkdir -p "$EVID"
status=0
cleanup() {
  python3 scripts/perf/close-owned-vm.py >/dev/null 2>&1
  python3 scripts/perf/restore-baseline-vm.py api29-r78 || status=7
  scripts/devlock.sh release lead-r80 || status=8
}
trap cleanup EXIT
scripts/devlock.sh acquire 1200 lead-r80 || { echo "WINDOW_REFUSED reason=lock"; exit 2; }
python3 scripts/perf/close-owned-vm.py || exit 4
$SSH 'ln -sfn /home/art/releases/api29-20261026-r80 /home/art/api29-root' || exit 5
echo "ROOT=$($SSH 'readlink /home/art/api29-root')"
bash scripts/sd.sh inputhold 100 2>&1 | tail -1
lipstick_state() { $SSH 'p=$(pidof lipstick); echo "$p|$(cut -d" " -f22 /proc/$p/stat 2>/dev/null)"' 2>/dev/null; }
for step in r80-swipe r80-qq-touch; do
  before=$(lipstick_state)
  python3 scripts/perf/run-matrix-vm.py r80 --only "$step" 2>&1 | grep -E "SDINPUT=finished|SDINPUT=swipe|swipes_|scene_driver|pump verdict|PERF_FILE" | head -20
  after=$(lipstick_state)
  echo "LIPSTICK step=$step before=$before after=$after" | tee -a "$EVID/lipstick2.log"
done
python3 scripts/perf/analyze-perf.py build/perf/r80-swipe-r80 2>&1 | grep -E "pump verdict|frames used|STATS"
python3 scripts/perf/analyze-perf.py build/perf/r80-qq-touch-r80 2>&1 | grep -E "pump verdict|frames used|STATS"
echo "WINDOW2_DONE status=$status"
exit $status
