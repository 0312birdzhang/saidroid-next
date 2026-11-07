#!/bin/sh
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
$SSH 'rm -rf /home/art/test/api29-deploy-whiteboard1 /home/art/test/api29-deploy-whiteboard2; echo PURGED; ls -d /home/art/test/api29-deploy-* 2>/dev/null | head; echo END; ls -1 /home/art/releases | wc -l; readlink /home/art/api29-root; df -h /home/art | tail -1'
