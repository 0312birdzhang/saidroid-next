#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- EGL/GLES providers:'; ls -la /usr/lib64/libEGL* /usr/lib64/libGLESv2* /usr/lib64/libgbm* 2>/dev/null | head -12; echo '--- dri drivers:'; ls /usr/lib64/dri 2>/dev/null | head -12; echo '--- mesa pkgs:'; rpm -qa 2>/dev/null | grep -i 'mesa\|llvmpipe\|swrast' | head -10; echo '--- hybris pkgs:'; rpm -qa 2>/dev/null | grep -i hybris | head -10; echo '--- surfaceless/llvmpipe strings:'; strings /usr/lib64/libEGL.so.1 2>/dev/null | grep -i 'surfaceless\|swrast\|llvmpipe' | head -5; echo '--- libEGL symlink target:'; readlink -f /usr/lib64/libEGL.so.1 2>/dev/null; readlink -f /usr/lib64/libGLESv2.so.2 2>/dev/null"
