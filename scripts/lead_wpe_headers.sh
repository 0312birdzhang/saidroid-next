#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- wpe-1.0 headers:'; ls /usr/include/wpe-1.0/wpe/ 2>/dev/null; echo '--- renderer-host header:'; ls -la /usr/include/wpe-1.0/wpe/renderer-host.h 2>/dev/null && grep -n 'wpe_renderer_host\|wpe_renderer_backend\|struct' /usr/include/wpe-1.0/wpe/renderer-host.h 2>/dev/null | head -30"
