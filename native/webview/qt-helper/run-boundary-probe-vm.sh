#!/bin/bash
# Exercise the exact staged native WebView host without waking the OLED.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../../.." && pwd)
label=${1:?unique-label}
release=${2:?staged-component-release}
[[ $label =~ ^[a-z0-9-]+$ && $release =~ ^api29-[a-z0-9-]+$ ]] || exit 2
export SSHPASS=${SSHPASS:?Set SSHPASS for device development}
mkdir -p "$repo/build/compat/$label"
bash "$repo/scripts/devlock.sh" acquire 0 codex-compat
cleanup(){
 sshpass -e ssh -o ConnectTimeout=6 root@bonito mcetool --blank-screen || true
 for name in host.log result.json; do sshpass -e scp -O -q -o ConnectTimeout=6 "root@bonito:/home/art/test/$label/$name" "$repo/build/compat/$label/$name" || true; done
 bash "$repo/scripts/devlock.sh" release codex-compat
}
trap cleanup EXIT
sshpass -e ssh -o ConnectTimeout=6 root@bonito /bin/cat /etc/sailfish-release
sshpass -e ssh -o ConnectTimeout=6 root@bonito /bin/cat /proc/sys/kernel/random/boot_id
sshpass -e ssh -o ConnectTimeout=6 root@bonito mcetool --blank-screen
timeout 110 sshpass -e ssh -o ConnectTimeout=6 root@bonito python3 - "$label" "$release" < "$repo/native/webview/qt-helper/boundary-probe-device.py"
