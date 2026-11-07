#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
echo "=== 看图器是否已退出 ==="
$SSH "pgrep sdview >/dev/null && echo RUNNING || echo EXITED; tail -3 /home/art/test/sdview.log"
echo "=== 取回帧 ==="
$SCP root@bonito:/home/art/view.rgba /tmp/ap/view.rgba
ls -l /tmp/ap/view.rgba
cp -f /tmp/ap/view.rgba /media/psf/Home/WorkSpace/saidroid-next/build/view.rgba
ls -l /media/psf/Home/WorkSpace/saidroid-next/build/view.rgba
