#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH 'echo "=== wpe-compat ==="; ls -la /usr/lib64/wpe-compat/ 2>&1 | head -20; echo "=== libWPEBackend* ==="; ls -la /usr/lib64/libWPEBackend* 2>&1; echo "=== eglplatform ==="; ls -la /usr/lib64/libhybris/ 2>&1 | head; echo "=== wpe-compat symbols ==="; for f in /usr/lib64/wpe-compat/*.so*; do [ -e "$f" ] || continue; echo "-- $f"; nm -D --defined-only "$f" 2>/dev/null | grep -E "wpe_renderer|wpe_view_backend|exportable|_wpe_" | head -20; done'
