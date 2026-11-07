#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- wayland-egl libs:'; ls -la /usr/lib64/libwayland-egl* 2>/dev/null; find /usr/lib64 -name 'libwayland-egl*' 2>/dev/null; echo '--- which pkg owns:'; rpm -qf /usr/lib64/libwayland-egl.so.1 2>/dev/null; echo '--- hybris wayland-egl symbols:'; nm -D --defined-only /usr/lib64/libwayland-egl.so.1 2>/dev/null | head -10; echo '--- ANativeWindow magic helper in egl:'; strings /usr/lib64/libEGL.so.1.0.0 2>/dev/null | grep -i 'wayland\|ANativeWindow\|native_window' | head -12"
