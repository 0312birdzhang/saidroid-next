#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SSH 'pkill -9 -f sdview2; pkill -9 -f LiveProbe; sleep 2; echo killed'
$SCP /tmp/sdview2/sdview root@bonito:/home/art/sdview2
$SSH 'rm -f /home/art/test/pattern.log
      export XDG_RUNTIME_DIR=/run/user/100000
      export WAYLAND_DISPLAY=../../display/wayland-0
      cd /home/art
      nohup ./sdview2 --pattern -t 60 /home/art/live.rgba > /home/art/test/pattern.log 2>&1 &
      echo started'
sleep 7
echo "=== 关键尺寸 ==="
$SSH "grep -a 'FRAME_LOADED\|TL_CONFIGURE\|OUT \|PATTERN\|VIEWER_READY' /home/art/test/pattern.log | head -14"
