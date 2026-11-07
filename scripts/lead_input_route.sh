#!/bin/bash
# 判定：Lipstick 把触摸投给谁？我们的 ART 窗口是不是它认为的"最上层可输入窗口"。
# 用法：lead_input_route.sh <run>
set -u
RUN=${1:?run}
REPO=/media/psf/Home/WorkSpace/saidroid-next
COMP=${COMP:-/var/tmp/saidroid-next-api29-component-r73}
PH="root@bonito"; export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SH="sshpass -e ssh -o StrictHostKeyChecking=no $PH"
SC="sshpass -e scp -o StrictHostKeyChecking=no"
OUT=$REPO/build/evidence/$RUN; mkdir -p $OUT

echo "=== 0. 前置：关掉所有 owned 进程 ==="
/bin/bash $REPO/scripts/lead_close_all.sh 2>&1 | tail -2

echo "=== 1. 安装 r66 ==="
python3 $REPO/scripts/api29/deploy-component.py $COMP $RUN 2>&1 | tail -2

echo "=== 2. 启动 QQ ==="
SD_PKG=com.tencent.mobileqq /bin/bash $REPO/scripts/sd.sh launch --wait 60 --env SAILDROID_DIAG_INPUT=1 --env SAILDROID_ANDROID_LOG_STDERR=1 2>&1 | tail -3
SD_PKG=com.tencent.mobileqq /bin/bash $REPO/scripts/sd.sh wait --wait 60 --marker SDWINDOW_SESSION=drawn 2>&1 | tail -1
ART=$(SD_PKG=com.tencent.mobileqq /bin/bash $REPO/scripts/sd.sh status 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('pid'))" 2>/dev/null)
echo "ART_PID=$ART"

echo "=== 3. Lipstick 认为的最上层窗口 PID ==="
TOPMOST=$($SH "su defaultuser -s /bin/sh -c 'export XDG_RUNTIME_DIR=/run/user/100000; export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket; gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId'" 2>&1)
echo "TOPMOST=$TOPMOST"

echo "=== 4. 点「登录」并看 native 有没有收到触摸 ==="
# 一次点一次；TAPXY 支持分号分隔的多步序列（"x1,y1;x2,y2"），每步之间留出界面响应时间。
for pair in $(printf '%s' "${TAPXY:-791,1900}" | tr ';' ' '); do
  TX=${pair%,*}; TY=${pair#*,}
  /bin/bash $REPO/scripts/sd.sh input tap "$TX" "$TY" 60
  sleep "${TAP_GAP:-2.5}"
done 2>&1 | tail -1
sleep 2
/bin/bash $REPO/scripts/sd.sh shot $RUN-after-login 2>&1 | tail -1

echo "=== 5. 日志 ==="
/bin/bash $REPO/scripts/sd.sh log -n 3000 > $OUT/app.log 2>&1
echo "LOG_LINES=$(wc -l < $OUT/app.log)"
echo "SDINPUT_LINES=$(grep -ac 'SDINPUT=' $OUT/app.log)"
grep -a 'SDINPUT=' $OUT/app.log | tr -d '\000' | head -5
echo "NPE_COUNT=$(grep -ac 'NullPointerException' $OUT/app.log)"

echo "=== 6. 关闭 + 恢复基线 ==="
/bin/bash $REPO/scripts/sd.sh close 2>&1 | tail -1
$SH "rm -f /home/art/api29-root && ln -s /home/art/releases/api29-20261026-r63 /home/art/api29-root && ls -l /home/art/api29-root | sed 's/.*-> //'"
