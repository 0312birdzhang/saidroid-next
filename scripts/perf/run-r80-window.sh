#!/bin/bash
# r80 evidence window: the optimised path is the DEFAULT now, so every r80-* step
# runs without an env flag. Deploys r80, runs the nine steps, then puts r78 back.
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
  echo "WINDOW_END status=$status root=$($SSH 'readlink /home/art/api29-root' 2>/dev/null)"
}
trap cleanup EXIT

scripts/devlock.sh acquire 3600 lead-r80 || { echo "WINDOW_REFUSED reason=lock"; exit 2; }
python3 scripts/perf/close-owned-vm.py || exit 4
python3 scripts/perf/deploy-perf-release-vm.py r80 || exit 5
echo "ROOT=$($SSH 'readlink /home/art/api29-root')"
# sdinput must be the current binary before the gesture steps, otherwise
# swipes_handled stays 0 and the P2 run proves nothing.
bash scripts/sd.sh inputhold 100 2>&1 | tail -2
bash scripts/sd.sh inputhold 100 2>&1 | tail -2

lipstick_state() { $SSH 'p=$(pidof lipstick); echo "$p|$(cut -d" " -f22 /proc/$p/stat 2>/dev/null)"' 2>/dev/null; }

for step in r80-scroll-1 r80-scroll-2 r80-scroll-3 r80-color r80-qq r80-qq-touch r80-swipe r80-gate-perf r80-gate-muted; do
  before=$(lipstick_state)
  echo "=== STEP $step lipstick_before=$before" | tee -a "$EVID/lipstick.log"
  python3 scripts/perf/run-matrix-vm.py r80 --only "$step" 2>&1 | tail -25
  rc=$?
  after=$(lipstick_state)
  echo "LIPSTICK step=$step before=$before after=$after" | tee -a "$EVID/lipstick.log"
  python3 - "$step" "$before" "$after" <<'PY' | tee -a "$EVID/lipstick.log"
import sys
step, before, after = sys.argv[1:4]
bp, bs = (before.split('|') + ['', ''])[:2]
ap, as_ = (after.split('|') + ['', ''])[:2]
if not ap:
    print('LIPSTICK_VERDICT|step=%s|WORST|lipstick_missing_after' % step)
elif bp != ap or bs != as_:
    print('LIPSTICK_VERDICT|step=%s|INVALID|lipstick_restarted %s/%s -> %s/%s' % (step, bp, bs, ap, as_))
else:
    print('LIPSTICK_VERDICT|step=%s|STABLE|pid=%s|ticks=%s' % (step, ap, as_))
PY
  if [ $rc -ne 0 ]; then echo "STEP_FAILED=$step rc=$rc"; status=6; break; fi
done

echo "=== RSS probe" | tee -a "$EVID/lipstick.log"
bash scripts/perf/r80-rss-vm.sh 2>&1 | tee "$EVID/rss.txt"

ls -1 build/perf/ | grep -- "-r80$" | tee "$EVID/runs.txt"
echo "WINDOW_DONE status=$status"
exit $status
