#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
echo "### tcp_check"
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/bonito/22' && echo "TCP22_OPEN" || echo "TCP22_CLOSED"
echo "### banner"
timeout 6 bash -c 'exec 3<>/dev/tcp/bonito/22; head -c 200 <&3' 2>&1 | head -5
echo "### ssh_verbose"
sshpass -e ssh -vv -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@bonito 'echo OK; cat /proc/sys/kernel/random/boot_id' 2>&1 | tail -25
echo "### ping"
ping -c 3 -W 2 bonito 2>&1 | tail -3
