#!/bin/bash
# 用真实的 uinput 触摸点击安装器里的「打开」按钮，验证 触摸->启动 这条链路
set -u
REPO=/media/psf/Home/WorkSpace/saidroid-next
S=$REPO/scripts/sd.sh
bash $REPO/scripts/devlock.sh acquire 200 || exit 1
trap 'bash $REPO/scripts/devlock.sh release >/dev/null 2>&1' EXIT
echo "=== 点击前 QQ 状态 ==="
bash $S status 2>&1 | head -3
echo "=== 注入 tap 到「打开」按钮 (203,454) ==="
bash $S input tap 203 454 80
echo "=== 等 6 秒后看状态 ==="
sleep 6
bash $S status 2>&1 | head -3
echo "=== 截图 ==="
bash $S shot lead-tap-open 2>&1 | tail -1
