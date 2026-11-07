#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "=== lock ==="
$SSH 'cat /home/art/test/.device-lock/owner 2>/dev/null || echo LOCK_FREE'
echo "=== root link ==="
$SSH 'readlink /home/art/api29-root'
echo "=== releases ==="
$SSH 'ls -1 /home/art/releases/ | tail -20'
echo "=== owned ==="
$SSH 'pgrep -af "saildroid|WPEWebProcess|WPENetworkProcess|wpe_offscreen" || echo NONE'
echo "=== disk ==="
$SSH 'df -h / | tail -1'
echo "=== staged deploy dirs ==="
$SSH 'ls -d /home/art/test/api29-deploy-* 2>/dev/null || echo NONE'
