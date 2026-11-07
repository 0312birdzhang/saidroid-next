#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
echo "=== 推 QQ native libs（202 个 / 334MB）==="
$SSH "mkdir -p /home/art/realapps/qq-libs /home/art/data/qq"
time sshpass -e scp -q -o StrictHostKeyChecking=no -r \
  /media/psf/Home/WorkSpace/saidroid-next/build/qq-libs/* root@bonito:/home/art/realapps/qq-libs/
$SSH "ls /home/art/realapps/qq-libs | wc -l; du -sh /home/art/realapps/qq-libs; df -h /home | tail -1"
