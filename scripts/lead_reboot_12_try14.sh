#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
for ip in 192.168.3.14 192.168.3.15; do
  echo "### $ip"
  sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@$ip 'echo OK; hostname; cat /proc/sys/kernel/random/boot_id; cut -d" " -f1 /proc/uptime; uname -a' 2>&1 | tail -6
done
