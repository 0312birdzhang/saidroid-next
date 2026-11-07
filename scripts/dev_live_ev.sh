#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
echo "=== 进程在不在 ==="
$SSH "pgrep -f LiveProbe >/dev/null && echo RUNNING || echo EXITED"
echo "=== 灌三个事件 ==="
$SSH 'printf "D 200 400\n" >> /home/art/events.txt; sleep 1;
      printf "M 300 600\n" >> /home/art/events.txt; sleep 1;
      printf "U\n" >> /home/art/events.txt; sleep 2; echo done'
echo "=== 标记 ==="
$SSH "grep -a 'LP\[' /home/art/test/live.log | tail -12"
echo "=== 帧文件的中心像素（应该已经变了）==="
$SSH "ls -l /home/art/live.rgba"
