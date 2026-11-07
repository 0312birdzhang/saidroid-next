#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- hybris wayland-egl files:'; rpm -ql libhybris-libwayland-egl 2>/dev/null; echo '--- hybris eglinfo dirs:'; ls -la /usr/lib64/hybris 2>/dev/null | head -20; echo '--- atlantic runtime-common.sh LD lines:'; grep -n 'LD_\|WAYLAND\|PRELOAD\|PATH' /opt/wpe-sfos/libexec/atlantic/runtime-common.sh 2>/dev/null | head -30"
