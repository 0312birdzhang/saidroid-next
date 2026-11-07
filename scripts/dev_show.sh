#!/bin/bash
# 在真机上用 sdview 把 view.rgba 贴到 Wayland 窗口（45 秒后自动退出）
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
$SSH 'export XDG_RUNTIME_DIR=/run/user/100000; \
      export WAYLAND_DISPLAY=../../display/wayland-0; \
      export LD_LIBRARY_PATH=/home/art/lib; \
      cd /home/art; \
      nohup ./sdview -t 45 -w 540 /home/art/view.rgba > /home/art/test/sdview.log 2>&1 & \
      echo started; sleep 6; head -20 /home/art/test/sdview.log'
