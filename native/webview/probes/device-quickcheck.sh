#!/bin/sh
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15 'cat /proc/sys/kernel/random/boot_id; readlink -f /home/art/api29-root; df -h /home/art | tail -1; ls -d /home/art/test/api29-deploy-* 2>/dev/null | head'
