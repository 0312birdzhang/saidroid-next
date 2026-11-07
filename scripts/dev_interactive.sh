#!/bin/bash
# 启动完整交互：LiveProbe 后台 + sdview --evfile --watch
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SCP /tmp/sdview2/sdview root@bonito:/home/art/sdview2

$SSH 'pkill -f LiveProbe; pkill -f sdview2; pkill -f "sdview -t"; sleep 1
      rm -f /home/art/events.txt /home/art/live.rgba /home/art/test/live.log /home/art/test/sdview2.log
      touch /home/art/events.txt; chmod 666 /home/art/events.txt
      . /home/art/env.sh
      cd /home/art/test
      nohup dalvikvm -cp /home/art/test/ap.dex LiveProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
            /home/art/events.txt /home/art/live.rgba 240 > /home/art/test/live.log 2>&1 &
      echo liveprobe-started'
sleep 22
$SSH 'export XDG_RUNTIME_DIR=/run/user/100000
      export WAYLAND_DISPLAY=../../display/wayland-0
      cd /home/art
      nohup ./sdview2 --watch --evfile /home/art/events.txt -t 200 -w 540 /home/art/live.rgba \
            > /home/art/test/sdview2.log 2>&1 &
      echo viewer-started'
sleep 8
echo "=== LiveProbe ==="
$SSH "grep -a 'LP\[' /home/art/test/live.log | grep -av 心跳 | head -10"
echo "=== 看图器 ==="
$SSH "head -12 /home/art/test/sdview2.log"
echo "=== 进程 ==="
$SSH "pgrep -f LiveProbe >/dev/null && echo liveprobe-RUNNING; pgrep -f sdview2 >/dev/null && echo viewer-RUNNING"
