#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
for ip in 192.168.3.15 bonito; do
  echo "### $ip"
  timeout 5 bash -c "exec 3<>/dev/tcp/$ip/22; head -c 50 <&3" 2>&1 | tr -d "\r" | head -2
  sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 -o NumberOfPasswordPrompts=1 root@$ip 'cat /proc/sys/kernel/random/boot_id; cut -d" " -f1 /proc/uptime; hostname' 2>&1 | tail -3
done
