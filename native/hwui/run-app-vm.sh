#!/bin/bash
# Serial, bounded device regression for the HWUI test APK.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
label=${1:?unique-label}
release=${2:?experimental-release-directory-name}
[[ $label =~ ^[a-z0-9-]+$ && $release =~ ^api29-[a-z0-9-]+$ ]] || exit 2
export SSHPASS=${SSHPASS:?Set SSHPASS for device development}
out=$repo/build/hwui
mkdir -p "$out"
bash "$repo/scripts/devlock.sh" acquire 0 codex-hwui
cleanup(){
 sshpass -e scp -O -q -o ConnectTimeout=8 "root@bonito:/home/art/test/$label.log" "$out/$label.log" || true
 for frame in before settled after dialog returned resume1 resume2; do sshpass -e scp -O -q -o ConnectTimeout=8 "root@bonito:/home/defaultuser/Downloads/SailDroid-Screenshots/$label-$frame.png" "$out/$label-$frame.png" || true; done
 bash "$repo/scripts/devlock.sh" release codex-hwui
}
trap cleanup EXIT
bash "$repo/native/hwui/prepare-health-vm.sh"
python3 "$repo/native/hwui/install-apk-vm.py" "${HWUI_APK_TAG:-hwui1}"
sshpass -e ssh -o ConnectTimeout=8 root@bonito python3 - "$label" "$release" "${HWUI_APP_MODE:-hardware}" < "$repo/native/hwui/run-app-device.py"
