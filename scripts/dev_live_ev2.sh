#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
sleep 6
echo "=== 心跳 ==="
$SSH "grep -a 'LP\[' /home/art/test/live.log | grep -a 心跳 | tail -4"
echo "=== 灌事件 ==="
$SSH 'printf "D 200 400\n" >> /home/art/events.txt; sleep 2; printf "M 300 600\n" >> /home/art/events.txt; sleep 2; printf "U\n" >> /home/art/events.txt; sleep 3; echo injected'
echo "=== 心跳/事件 ==="
$SSH "grep -a 'LP\[' /home/art/test/live.log | tail -8"
echo "=== 帧 mtime ==="
$SSH "ls -l /home/art/live.rgba"
