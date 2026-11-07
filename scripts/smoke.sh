#!/bin/bash
# 冒烟：确认设备、当前安装版本、QQ 能否起来
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "=== 设备 ==="
$SSH "cat /etc/sailfish-release 2>/dev/null | head -2; uptime | tr -s ' '"
echo "=== 当前安装 ==="
$SSH "readlink -f /home/art/api29-root; ls -l /home/art/api29-root | head -2"
echo "=== 运行态 ==="
$SSH "pgrep -af 'saildroid|dalvikvm' | head -5 || echo '(没有运行中的实例)'"
