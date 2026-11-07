#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../../.." && pwd)
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
bash "$repo/scripts/devlock.sh" acquire 0 codex-webview-fix
base=$(sshpass -e ssh -o ConnectTimeout=6 root@bonito 'readlink -f /home/art/api29-root')
label=${2:?unique-label}
release=${1:?staged-release}
[[ $label =~ ^[a-z0-9-]+$ && $release =~ ^api29-[a-z0-9-]+$ ]] || exit 2
mkdir -p "$repo/build/qq-startup-webview"
cleanup(){
 sshpass -e ssh -o ConnectTimeout=6 root@bonito mcetool --blank-screen || true
 sshpass -e scp -O -q -o ConnectTimeout=6 "root@bonito:/home/art/test/$label.log" "$repo/build/qq-startup-webview/$label.log" || true
 for frame in before after; do sshpass -e scp -O -q -o ConnectTimeout=6 "root@bonito:/home/defaultuser/Downloads/SailDroid-Screenshots/$label-$frame.png" "$repo/build/qq-startup-webview/$label-$frame.png" || true;done
 python3 "$repo/scripts/perf/close-owned-vm.py" || true
 sshpass -e ssh -o ConnectTimeout=6 root@bonito "ln -s '$base' /home/art/.r86-web-restore && mv -Tf /home/art/.r86-web-restore /home/art/api29-root"
 bash "$repo/scripts/devlock.sh" release codex-webview-fix
}
trap cleanup EXIT
python3 "$repo/scripts/perf/close-owned-vm.py"
sshpass -e ssh -o ConnectTimeout=6 root@bonito "ln -s /home/art/releases/$release /home/art/.r86-web-test && mv -Tf /home/art/.r86-web-test /home/art/api29-root"
python3 "$repo/native/webview/qt-helper/install-probe-apk-vm.py" "${SD_WEBVIEW_APK_TAG:-r86-verification2}"
sshpass -e scp -O -q -o ConnectTimeout=6 "$repo/native/webview/qt-helper/verification-server.py" root@bonito:/home/art/test/verification-server-r86.py
sshpass -e ssh -o ConnectTimeout=6 root@bonito chmod 644 /home/art/test/verification-server-r86.py
sshpass -e ssh -o ConnectTimeout=6 root@bonito python3 - "$label" < "$repo/native/webview/qt-helper/verification-probe-device.py"
