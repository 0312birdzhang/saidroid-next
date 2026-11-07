#!/bin/bash
# 留一个较长的可交互会话，方便用真手指点
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
$SSH 'pkill -9 -f LiveProbe; pkill -9 -f sdview2; sleep 2
      rm -f /home/art/events.txt /home/art/live.rgba /home/art/test/live.log /home/art/test/sdview2.log
      touch /home/art/events.txt; chmod 666 /home/art/events.txt
      . /home/art/env.sh; cd /home/art/test
      nohup dalvikvm -cp /home/art/test/ap.dex LiveProbe /home/art/bio2 /home/art/lib/libsdbridge.so \
            /home/art/events.txt /home/art/live.rgba 400 > /home/art/test/live.log 2>&1 &
      echo liveprobe-ok'
sleep 24
$SSH 'export XDG_RUNTIME_DIR=/run/user/100000
      export WAYLAND_DISPLAY=../../display/wayland-0
      cd /home/art
      nohup ./sdview2 --watch --evfile /home/art/events.txt -t 360 -w 540 /home/art/live.rgba \
            > /home/art/test/sdview2.log 2>&1 &
      echo viewer-ok'
sleep 6
$SSH 'pgrep -f LiveProbe >/dev/null && echo "LiveProbe RUNNING"; pgrep -f sdview2 >/dev/null && echo "Viewer RUNNING"; grep -a "VIEWER_READY\|VIEWER_WATCHING\|VIEWER_EVFILE" /home/art/test/sdview2.log'
