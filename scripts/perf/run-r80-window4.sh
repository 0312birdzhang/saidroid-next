#!/bin/bash
# r80 fourth window: gesture delivery with ONE uinput device (serve) versus one
# device per swipe. lipstick died in window3 during the per-swipe run, so this is
# also the A/B on whether that churn is what kills it. lipstick is sampled every
# 3 s while a step runs, because journal retention here is only ~3 minutes.
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
scripts/devlock.sh acquire 1800 lead-r80 || { echo "WINDOW_REFUSED reason=lock"; exit 2; }
python3 scripts/perf/close-owned-vm.py || exit 4
$SSH 'ln -sfn /home/art/releases/api29-20261026-r80 /home/art/api29-root' || exit 5
echo "ROOT=$($SSH 'readlink /home/art/api29-root')"

sample_lipstick() {
  while :; do
    $SSH 'p=$(pidof lipstick); echo "$(date +%H:%M:%S) $p $(cut -d" " -f22 /proc/$p/stat 2>/dev/null)"' >> "$EVID/lipstick-samples.log" 2>/dev/null
    sleep 3
  done
}

for step in r80-swipe-serve r80-swipe; do
  before=$($SSH 'p=$(pidof lipstick); echo "$p|$(cut -d" " -f22 /proc/$p/stat)"')
  echo "STEP_BEGIN $step lipstick=$before" | tee -a "$EVID/lipstick4.log"
  sample_lipstick & sampler=$!
  python3 scripts/perf/run-matrix-vm.py r80 --only "$step" 2>&1 | grep -E "SDINPUT=finished|swipes_|scene_driver|PERF_FILE" | head -20
  kill $sampler 2>/dev/null; wait $sampler 2>/dev/null
  after=$($SSH 'p=$(pidof lipstick); echo "$p|$(cut -d" " -f22 /proc/$p/stat)"')
  echo "STEP_END $step lipstick=$after" | tee -a "$EVID/lipstick4.log"
  $SSH 'journalctl -b --no-pager 2>/dev/null | tail -300' > "$EVID/journal-$step.log" 2>/dev/null
  python3 - "$step" "$before" "$after" <<'PY' | tee -a "$EVID/lipstick4.log"
import sys
step, before, after = sys.argv[1:4]
bp, bs = (before.split('|') + ['', ''])[:2]
ap, as_ = (after.split('|') + ['', ''])[:2]
if not ap:
    print('LIPSTICK_VERDICT|step=%s|INVALID|lipstick_gone_after' % step)
elif (bp, bs) != (ap, as_):
    print('LIPSTICK_VERDICT|step=%s|INVALID|restarted %s/%s -> %s/%s' % (step, bp, bs, ap, as_))
else:
    print('LIPSTICK_VERDICT|step=%s|STABLE|pid=%s|ticks=%s' % (step, ap, as_))
PY
done
for d in r80-swipe-serve-r80 r80-swipe-r80; do
  python3 scripts/perf/analyze-perf.py "build/perf/$d" 2>&1 | grep -E "pump verdict|frames used|STATS"
done
echo "WINDOW4_DONE status=$status"
exit $status
