#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- helper_library_path fn:'; sed -n '/atlantic_default_helper_library_path/,/^}/p' /opt/wpe-sfos/libexec/atlantic/runtime-common.sh 2>/dev/null | head -30; echo '--- HYBRIS/EGL refs in script:'; grep -n -i 'hybris\|EGL_PLATFORM\|eglplatform' /opt/wpe-sfos/libexec/atlantic/runtime-common.sh 2>/dev/null | head -20; echo '--- atlantic binfiles:'; ls /opt/wpe-sfos/libexec/atlantic/ 2>/dev/null | head -20"
