#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
echo "### ping_old_ip"
ping -c 2 -W 2 bonito 2>&1 | tail -3
echo "### ssh_try"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito 'cat /proc/sys/kernel/random/boot_id; cut -d" " -f1 /proc/uptime' 2>&1 | tail -3
echo "### arp"
ip neigh 2>/dev/null | head -20
echo "### vm_ip"
ip -4 addr show | grep -E "inet " | head
