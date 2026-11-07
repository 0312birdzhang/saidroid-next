#!/bin/bash
echo "=== 重新配置 RNDIS ==="
/root/bonito-deploy/private/20260829T164009Z-login-visibility-install/ensure_rndis_debug.sh --apply 2>&1 | tail -3
sleep 2
echo "=== 连通性 ==="
ping -c 2 -W 2 bonito 2>&1 | tail -2
echo "=== SSH ==="
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito 'echo SSH_OK; uptime; free -m | head -2' 2>&1 | tail -5
