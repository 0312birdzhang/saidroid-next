#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH 'echo "boot_id=$(cat /proc/sys/kernel/random/boot_id)"; echo "uptime=$(cut -d. -f1 /proc/uptime)"; echo "lipstick=$(pgrep -f /usr/bin/lipstick | tr "\n" " ")"; echo "rootlink=$(readlink /home/art/api29-root)"; echo "lock=$(cat /home/art/test/.device-lock/owner 2>/dev/null)"; echo "load=$(cat /proc/loadavg)"; echo "mem=$(free -m | sed -n 2p)"'
