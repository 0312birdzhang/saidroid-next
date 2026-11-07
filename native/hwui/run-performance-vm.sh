#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
label=${1:?unique-label};release=${2:?release-name}
[[ $label =~ ^[a-z0-9-]+$ && $release =~ ^api29-[a-z0-9-]+$ ]] || exit 2
export SSHPASS=${SSHPASS:?Set SSHPASS for device development}
out=$repo/build/hwui;mkdir -p "$out"
bash "$repo/scripts/devlock.sh" acquire 0 codex-hwui
cleanup(){
 for suffix in log json; do sshpass -e scp -O -q -o ConnectTimeout=8 "root@bonito:/home/art/test/$label.$suffix" "$out/$label.$suffix" || true; done
 bash "$repo/scripts/devlock.sh" release codex-hwui
}
trap cleanup EXIT
bash "$repo/native/hwui/prepare-health-vm.sh"
python3 "$repo/scripts/perf/install-scroll-vm.py" "${HWUI_PERF_APK_TAG:-hwui1}"
sshpass -e ssh -o ConnectTimeout=8 root@bonito python3 - "$label" "$release" < "$repo/native/hwui/run-performance-device.py"
