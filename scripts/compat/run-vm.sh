#!/bin/bash
# Run from the build VM; all component changes are temporary.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
label=${1:?unique-label}
release=${2:?staged-release}
tag=${3:?built-apk-tag}
[[ $label =~ ^[a-z0-9-]+$ && $release =~ ^api29-[a-z0-9-]+$ && $tag =~ ^[a-z0-9-]+$ ]] || exit 2
export SSHPASS=${SSHPASS:?Set SSHPASS for device development}
mkdir -p "$repo/build/compat"
bash "$repo/scripts/devlock.sh" acquire 0 codex-compat
cleanup(){
 sshpass -e ssh -o ConnectTimeout=6 root@bonito mcetool --blank-screen || true
 sshpass -e scp -O -q -o ConnectTimeout=8 "root@bonito:/home/art/test/$label.log" "$repo/build/compat/$label.log" || true
 bash "$repo/scripts/devlock.sh" release codex-compat
}
trap cleanup EXIT
sshpass -e ssh -o ConnectTimeout=8 root@bonito /bin/cat /etc/sailfish-release
sshpass -e ssh -o ConnectTimeout=8 root@bonito /bin/cat /proc/sys/kernel/random/boot_id
python3 "$repo/scripts/perf/close-owned-vm.py"
bash "$repo/native/hwui/prepare-health-vm.sh"
python3 "$repo/scripts/compat/install-apk-vm.py" "$tag"
sshpass -e ssh -o ConnectTimeout=8 root@bonito python3 - "$label" "$release" < "$repo/scripts/compat/run-device.py"
