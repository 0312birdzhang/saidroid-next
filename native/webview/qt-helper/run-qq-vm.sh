#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
release=${1:?existing-release};label=${2:?unique-label}
[[ $release =~ ^api29-[a-z0-9-]+$ && $label =~ ^[a-z0-9-]+$ ]] || exit 2
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
ssh=(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito)
scp=(sshpass -e scp -q -o StrictHostKeyChecking=no -o ConnectTimeout=8)
cd "$repo";out=$repo/build/evidence/$label;mkdir -p "$out"
bash scripts/devlock.sh acquire 0 codex-webview
base=$("${ssh[@]}" 'readlink -f /home/art/api29-root')
cleanup() {
  "${ssh[@]}" 'mcetool --blank-screen' || true
  "${scp[@]}" "root@bonito:/home/art/test/$label-app.log" "$out/app.log" 2>/dev/null || true
  python3 scripts/perf/close-owned-vm.py > "$out/close.log" 2>&1 || true
  "${ssh[@]}" "ln -s '$base' /home/art/.api29-root-codex-restore && mv -Tf /home/art/.api29-root-codex-restore /home/art/api29-root"
  bash scripts/devlock.sh release codex-webview
}
trap cleanup EXIT
python3 scripts/perf/close-owned-vm.py
"${ssh[@]}" "test -x /home/art/releases/$release/libexec/sdwebview-host && ln -s /home/art/releases/$release /home/art/.api29-root-codex-test && mv -Tf /home/art/.api29-root-codex-test /home/art/api29-root"
"${ssh[@]}" "python3 - '$label'" < "$repo/native/webview/qt-helper/qq-probe-device.py" | tee "$out/result.txt"
"${scp[@]}" "root@bonito:/home/art/test/$label-app.log" "$out/app.log"
for n in login help h5; do "${scp[@]}" "root@bonito:/home/defaultuser/Downloads/SailDroid-Screenshots/$label-$n.png" "$out/$n.png" 2>/dev/null || true; done

python3 native/webview/qt-helper/check-qq-frame.py "$out/h5.png" | tee "$out/pixels.json"
echo "QQ_WEBVIEW_SUITE=ready|run=$label"
