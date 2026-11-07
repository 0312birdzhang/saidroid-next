#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
REPO=/media/psf/Home/WorkSpace/saidroid-next
H=root@bonito
mkdir -p "$REPO/build/evidence"
mkdir -p "$REPO/build/logs"
sshpass -e ssh -o StrictHostKeyChecking=no $H "tar cf - -C /home/art/data/logs/com.tencent.mobileqq \$(ls -t /home/art/data/logs/com.tencent.mobileqq | head -4)" 2>/dev/null | tar xf - -C "$REPO/build/evidence"
ls -lt "$REPO/build/evidence" | head -6
