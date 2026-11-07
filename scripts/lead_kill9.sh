#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "=== 状态 ==="
$SSH "ps -o pid,ppid,stat,args -p 40798,40800,40844 2>/dev/null | cut -c1-110"
echo "=== SIGKILL ==="
$SSH "kill -9 40844 40800 40798 2>/dev/null; sleep 2; echo killed"
echo "=== 复查 ==="
$SSH "ps -o pid,stat,args -p 40800,40844 2>/dev/null | cut -c1-100; pgrep -af 'atlantic-browser|WPEWebProcess' | cut -c1-100; echo END"
