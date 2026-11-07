#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
label=${1:?unique-label};release=${2:?experimental-release-name};probe=${3:-HwuiWindowProbe}
[[ $label =~ ^[a-z0-9-]+$ && $release =~ ^api29-[a-z0-9-]+$ ]] || exit 2
export SSHPASS=${SSHPASS:?Set SSHPASS for device development}
out=$repo/build/hwui;mkdir -p "$out"
bash "$repo/scripts/devlock.sh" acquire 0 codex-hwui
cleanup(){
 sshpass -e scp -O -q -o ConnectTimeout=8 "root@bonito:/home/art/test/$label.log" "$out/$label.log" || true
 sshpass -e scp -O -q -o ConnectTimeout=8 "root@bonito:/home/defaultuser/Downloads/SailDroid-Screenshots/$label.png" "$out/$label.png" || true
 bash "$repo/scripts/devlock.sh" release codex-hwui
}
trap cleanup EXIT
bash "$repo/native/hwui/prepare-health-vm.sh"
sshpass -e scp -O -q -o ConnectTimeout=8 "$out/standalone-probes/probe.jar" root@bonito:/home/art/test/hwui-standalone-probe.jar
sshpass -e ssh -o ConnectTimeout=8 root@bonito chmod 644 /home/art/test/hwui-standalone-probe.jar
sshpass -e ssh -o ConnectTimeout=8 root@bonito python3 - "$label" "$release" "$probe" < "$repo/native/hwui/run-probe-device.py"
