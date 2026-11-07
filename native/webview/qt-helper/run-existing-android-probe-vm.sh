#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
release=${1:?existing-release}
label=${2:?unique-label}
[[ $release =~ ^api29-[a-z0-9-]+$ && $label =~ ^[a-z0-9-]+$ ]] || exit 2
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}" SD_PKG=org.example.saildroid.webviewprobe
ssh=(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito)
scp=(sshpass -e scp -q -o StrictHostKeyChecking=no -o ConnectTimeout=8)
cd "$repo";out=$repo/build/evidence/$label;mkdir -p "$out"
bash scripts/devlock.sh acquire 0 codex-webview
base=$("${ssh[@]}" 'readlink -f /home/art/api29-root')
cleanup() {
  "${ssh[@]}" 'mcetool --blank-screen' || true
  python3 scripts/perf/close-owned-vm.py > "$out/close.log" 2>&1 || true
  "${ssh[@]}" "ln -s '$base' /home/art/.api29-root-codex-restore && mv -Tf /home/art/.api29-root-codex-restore /home/art/api29-root"
  bash scripts/devlock.sh release codex-webview
}
trap cleanup EXIT
python3 scripts/perf/close-owned-vm.py
"${ssh[@]}" "test -x /home/art/releases/$release/libexec/sdwebview-host && ln -s /home/art/releases/$release /home/art/.api29-root-codex-test && mv -Tf /home/art/.api29-root-codex-test /home/art/api29-root"
"${ssh[@]}" "python3 - '$label'" < "$repo/native/webview/qt-helper/crash-probe-device.py" | tee "$out/result.txt"
"${scp[@]}" "root@bonito:/home/art/test/$label-app.log" "$out/app.log"
