#!/bin/bash
# 端到端：真实触摸注入 -> Wayland -> sdview -> events.txt -> LiveProbe -> 重画 -> sdview 重载
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"

echo "=== 1. 彻底清理 ==="
$SSH 'pkill -9 -f LiveProbe; pkill -9 -f sdview2; pkill -9 -f "sdview -t"; sleep 2
      pgrep -af "LiveProbe|sdview" | head -3; echo cleaned'

$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SCP /tmp/sdview2/sdview root@bonito:/home/art/sdview2

echo "=== 2. 起 LiveProbe ==="
$SSH 'rm -f /home/art/events.txt /home/art/live.rgba /home/art/test/live.log /home/art/test/sdview2.log
      touch /home/art/events.txt; chmod 666 /home/art/events.txt
      . /home/art/env.sh; cd /home/art/test
      nohup dalvikvm -cp /home/art/test/ap.dex LiveProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
            /home/art/events.txt /home/art/live.rgba 200 > /home/art/test/live.log 2>&1 &
      echo ok'
sleep 24

echo "=== 3. 起看图器（--watch --evfile）==="
$SSH 'export XDG_RUNTIME_DIR=/run/user/100000
      export WAYLAND_DISPLAY=../../display/wayland-0
      cd /home/art
      nohup ./sdview2 --watch --evfile /home/art/events.txt -t 150 -w 540 /home/art/live.rgba \
            > /home/art/test/sdview2.log 2>&1 &
      echo ok'
sleep 8

echo "=== 4. 注入真实触摸 (270,540) ==="
$SSH '/home/art/inject_touch 270 540 > /home/art/test/inject.log 2>&1; echo "inject rc=$?"'
sleep 4

echo "=== 5. 结果 ==="
echo "--- events.txt ---"
$SSH "cat /home/art/events.txt"
echo "--- 看图器触摸日志 ---"
$SSH "grep -a 'TOUCH\|PTR' /home/art/test/sdview2.log | tail -8"
echo "--- LiveProbe 心跳 ---"
$SSH "grep -a 心跳 /home/art/test/live.log | tail -2"
echo "--- 帧状态 ---"
$SSH "stat -c '被写于 %y' /home/art/live.rgba; od -An -tx4 -j \$((15 + (540*540 + 270)*4)) -N 4 /home/art/live.rgba"
