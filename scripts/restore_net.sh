#!/bin/bash
echo "=== 重新配置 RNDIS ==="
/root/bonito-deploy/private/20260829T164009Z-login-visibility-install/ensure_rndis_debug.sh --apply 2>&1 | tail -3
sleep 3
echo "=== 连通性 ==="
ping -c 2 -W 2 bonito 2>&1 | tail -2
echo "=== SSH + 设备状态 ==="
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito \
'echo SSH_OK
cat /proc/sys/kernel/random/boot_id
uptime
free -m | head -3
df -h /tmp | tail -1' 2>&1 | tail -10
