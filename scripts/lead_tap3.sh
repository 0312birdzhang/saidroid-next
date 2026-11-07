#!/bin/bash
# 在「已经部署好并指向 api29-root」的组件上跑一次「启动 → 按 TAPXY 序列点击 → 截图 → 拉日志 → 关闭」。
# 用法：TAPXY="791,1900;1005,152;400,1803" bash scripts/lead_tap3.sh npe24
set -u
RUN=${1:?run}
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT=$REPO/build/evidence/$RUN; mkdir -p $OUT
PKG=com.tencent.mobileqq

echo "=== 1. 启动 ==="
SD_PKG=$PKG /bin/bash $REPO/scripts/sd.sh launch --wait 60 --env SAILDROID_DIAG_INPUT=1 --env SAILDROID_ANDROID_LOG_STDERR=1 2>&1 | tail -2
SD_PKG=$PKG /bin/bash $REPO/scripts/sd.sh wait --wait 60 --marker SDWINDOW_SESSION=drawn 2>&1 | tail -1

echo "=== 2. 点击序列 ==="
for pair in $(printf '%s' "${TAPXY:-791,1900}" | tr ';' ' '); do
  TX=${pair%,*}; TY=${pair#*,}
  echo "TAP $TX,$TY"
  /bin/bash $REPO/scripts/sd.sh input tap "$TX" "$TY" 60 2>&1 | tail -1
  sleep "${TAP_GAP:-3.0}"
done
sleep 2
/bin/bash $REPO/scripts/sd.sh shot $RUN-after 2>&1 | tail -1

echo "=== 3. 日志 ==="
/bin/bash $REPO/scripts/sd.sh log -n 4000 > $OUT/app.log 2>&1
echo "LOG_LINES=$(wc -l < $OUT/app.log)"
grep -a 'SDINPUT=finished' $OUT/app.log | tr -d '\000' | tail -4
grep -a 'SDACTIVITY=launched' $OUT/app.log | tr -d '\000' | tail -4
grep -a 'SDRUNTIME=failed\|SDLAUNCHER=' $OUT/app.log | tr -d '\000' | tail -3
echo "FATAL_NPE=$(grep -ac 'MarginLayoutParams.leftMargin' $OUT/app.log)"
echo "VIEWGROUP_LINE=$(grep -a -A1 'MarginLayoutParams.leftMargin' $OUT/app.log | tr -d '\000' | grep -a 'at android.view.ViewGroup' | head -1)"

echo "=== 4. 关闭 ==="
/bin/bash $REPO/scripts/sd.sh close 2>&1 | tail -1
