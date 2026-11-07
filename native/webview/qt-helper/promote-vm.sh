#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
release=${1:?verified-release-name}
[[ $release =~ ^api29-[a-z0-9-]+$ ]] || exit 2
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
cd "$repo"
bash scripts/devlock.sh acquire 0 codex-promote
trap 'bash scripts/devlock.sh release codex-promote' EXIT
python3 scripts/perf/close-owned-vm.py
sshpass -e ssh -o ConnectTimeout=8 root@bonito "python3 - '$release'" < native/webview/qt-helper/cleanup-and-promote-device.py
sshpass -e ssh -o ConnectTimeout=8 root@bonito /bin/sh <<'PHONE'
set -eu
sleep 1
gdbus call --system --dest com.nokia.mce --object-path /com/nokia/mce/request --method com.nokia.mce.request.get_display_status
cat /sys/class/backlight/panel0-backlight/actual_brightness
pidof lipstick
cat /proc/sys/kernel/random/boot_id
ssu status | head -8
PHONE
