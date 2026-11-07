#!/bin/bash
# Lead 的一手基线：真实启动 QQ，记录耗时、画面上屏、生命周期标记
set -u
REPO=/media/psf/Home/WorkSpace/saidroid-next
S=$REPO/scripts/sd.sh
echo "=== 拿锁 ==="
$S >/dev/null 2>&1 || true
bash $REPO/scripts/devlock.sh acquire 300 || exit 1
trap 'bash $REPO/scripts/devlock.sh release >/dev/null 2>&1' EXIT

echo "=== 关闭残留 ==="
bash $S close 2>&1 | tail -2
sleep 2

echo "=== 启动（计时）==="
start=$(date +%s.%N)
bash $S launch --wait 90 2>&1 | tail -3
bash $S wait --wait 90 --marker SDWINDOW_SESSION=drawn 2>&1 | tail -2
end=$(date +%s.%N)
echo "STARTUP_SECONDS=$(echo "$end - $start" | bc)"

echo "=== 生命周期/窗口标记 ==="
bash $S log -n 400 2>/dev/null | grep -aE "SDACTIVITY|SDWINDOW_SESSION|SDWINDOW|resumed|SDHOST" | tail -20

echo "=== 截图 ==="
bash $S shot lead-qq-baseline 2>&1 | tail -2
