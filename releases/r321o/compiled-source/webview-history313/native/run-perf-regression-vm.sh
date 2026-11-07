#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
release=${1:?candidate-release};label=${2:?unique-label}
[[ $release =~ ^api29-[a-z0-9-]+$ && $label =~ ^[a-z0-9-]+$ ]] || exit 2
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
ssh=(sshpass -e ssh -o ConnectTimeout=8 root@bonito)
cd "$repo";mkdir -p "build/evidence/$label"
bash scripts/devlock.sh acquire 0 codex-perf
base=$("${ssh[@]}" 'readlink -f /home/art/api29-root')
cleanup() {
  "${ssh[@]}" 'mcetool --blank-screen' || true
  python3 scripts/perf/close-owned-vm.py > "build/evidence/$label/close.log" 2>&1 || true
  "${ssh[@]}" "ln -s '$base' /home/art/.api29-root-codex-restore && mv -Tf /home/art/.api29-root-codex-restore /home/art/api29-root"
  bash scripts/devlock.sh release codex-perf
}
trap cleanup EXIT
python3 scripts/perf/close-owned-vm.py
for variant in legacy candidate; do
  python3 scripts/perf/close-owned-vm.py
  selected=api29-r78
  [ "$variant" != candidate ] || selected=$release
  "${ssh[@]}" "test -d '/home/art/releases/$selected' && ln -s '/home/art/releases/$selected' /home/art/.api29-root-codex-perf && mv -Tf /home/art/.api29-root-codex-perf /home/art/api29-root"
  before=$("${ssh[@]}" 'p=$(pidof lipstick); echo "$p|$(cut -d" " -f22 /proc/$p/stat)"')
  "${ssh[@]}" "python3 - '$label-$variant'" <<'PYWATCH'
import subprocess,sys
from pathlib import Path
label=sys.argv[1]
p=subprocess.Popen(['/bin/sh','-c','sleep 35; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
Path('/home/art/test/'+label+'-display-watch.pid').write_text(str(p.pid))
subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True)
PYWATCH
  # Only the bounded observation window is lit; failure cleanup blanks it too.
  python3 scripts/perf/run-perf-vm.py --tag "$label-$variant" --scenario scroll --mode heavy --driver handler --window 8 --warmup 3
  "${ssh[@]}" "python3 - '$label-$variant'" <<'PYWATCH'
import subprocess,sys,os,signal
from pathlib import Path
subprocess.run(['mcetool','--blank-screen'],check=True)
path=Path('/home/art/test/'+sys.argv[1]+'-display-watch.pid')
if path.exists():
 pid=int(path.read_text())
 try:os.killpg(pid,signal.SIGTERM)
 except ProcessLookupError:pass
 path.unlink()
PYWATCH
  after=$("${ssh[@]}" 'p=$(pidof lipstick); echo "$p|$(cut -d" " -f22 /proc/$p/stat)"')
  [ "$before" = "$after" ] || { echo 'PERF_INVALID=lipstick_restarted';exit 3; }
  python3 scripts/perf/analyze-perf.py "build/perf/$label-$variant" > "build/evidence/$label/$variant-analysis.txt"
done
