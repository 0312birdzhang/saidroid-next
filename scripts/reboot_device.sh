#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
echo "=== 重启前的 boot id ==="
$SSH 'cat /proc/sys/kernel/random/boot_id; uptime' 2>&1 | tail -3
echo
echo "=== 执行重启 ==="
$SSH 'sync; (sleep 2; reboot) > /dev/null 2>&1 &' 2>&1 | tail -2
echo "REBOOT_ISSUED"
