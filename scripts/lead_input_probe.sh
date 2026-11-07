#!/bin/bash
# 只读探针：为什么 uinput 注入的触摸没生效（在 VM 里跑，内部 ssh 到手机）
SSHPASS="${SSHPASS:?Set SSHPASS for device development}" sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'bash -s' <<'REMOTE'
# 只读探针：为什么 uinput 注入的触摸没生效
echo "=== /proc/bus/input/devices ==="
cat /proc/bus/input/devices | tr -d '\000'
echo "=== /dev/input 节点 ==="
ls -l /dev/input/
echo "=== lipstick 打开的设备 ==="
for p in $(pgrep -f '/usr/bin/lipstick'); do echo "pid=$p"; ls -l /proc/$p/fd 2>/dev/null | grep -E 'input|event' ; done
echo "=== 有无 udev ==="
ps -ef | grep -E 'udev|systemd-udevd' | grep -v grep | head -3
echo "=== compositor 网络 ==="
ls -l /run/user/100000/wayland-0 2>/dev/null

REMOTE
