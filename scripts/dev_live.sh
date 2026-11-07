#!/bin/bash
# 启动 LiveProbe（后台）+ sdview（带 --evfile/--watch），然后用脚本灌几个事件验证链路
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"

$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SCP /tmp/sdview2/sdview root@bonito:/home/art/sdview2

$SSH 'rm -f /home/art/events.txt /home/art/live.rgba /home/art/test/live.log /home/art/test/sdview2.log
      touch /home/art/events.txt
      . /home/art/env.sh
      cd /home/art/test
      nohup dalvikvm -cp /home/art/test/ap.dex LiveProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
            /home/art/events.txt /home/art/live.rgba 100 > /home/art/test/live.log 2>&1 &
      echo liveprobe-started'
sleep 25
echo "=== LiveProbe 启动情况 ==="
$SSH "grep -a 'LP\[' /home/art/test/live.log | head -12"
echo "=== live.rgba ==="
$SSH "ls -l /home/art/live.rgba 2>/dev/null"
