#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
release=${1:?release-name};label=${2:?unique-label}
[[ $release =~ ^api29-[a-z0-9-]+$ && $label =~ ^[a-z0-9-]+$ ]] || exit 2
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
cd "$repo";mkdir -p "build/evidence/$label"
bash scripts/devlock.sh acquire 0 codex-webview
trap 'bash scripts/devlock.sh release codex-webview' EXIT
sshpass -e ssh -o ConnectTimeout=8 root@bonito "python3 - /home/art/releases/$release '$label'" < native/webview/qt-helper/idle-probe-device.py | tee "build/evidence/$label/result.json"
