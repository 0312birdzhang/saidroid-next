#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
{
echo "### time"; date -Is
echo "### tcp"; timeout 4 bash -c 'cat < /dev/null > /dev/tcp/bonito/22' && echo OPEN || echo CLOSED
echo "### banner"; timeout 5 bash -c 'exec 3<>/dev/tcp/bonito/22; head -c 60 <&3' 2>&1 | tr -d "\r" | head -2
echo "### ssh"; sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 -o NumberOfPasswordPrompts=1 root@bonito 'cat /proc/sys/kernel/random/boot_id; cut -d" " -f1 /proc/uptime' 2>&1 | tail -3
} > /tmp/probe8.out 2>&1
cat /tmp/probe8.out
