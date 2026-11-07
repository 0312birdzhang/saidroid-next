#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- atlantic pkgs:'; rpm -qa 2>/dev/null | grep -i 'atlantic\|wpe' | head -20; echo '--- wpe-fdo headers:'; ls /usr/include/wpe-fdo-1.0/wpe/ 2>/dev/null; echo '--- offscreen symbols in fdo backend:'; for f in /usr/lib64/libWPEBackend-fdo-1.0.so.1*; do echo \"\$f\"; nm -D --defined-only \$f 2>/dev/null | grep -i 'offscreen\|renderer_backend\|renderer_host' | head -20; done; echo '--- offscreen symbols in libwpe:'; nm -D --defined-only /usr/lib64/libwpe-1.0.so.1* 2>/dev/null | grep -i 'offscreen' | head -20; echo '--- wpe-compat:'; ls -la /usr/lib64/wpe-compat/ 2>/dev/null | head"
