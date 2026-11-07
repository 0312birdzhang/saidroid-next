#!/bin/bash
# Lead 的 NPE 复现窗口 v2：装 r64 → 启 QQ → 点「登录」→ 等 QQBrowserActivity 崩 → 抓 View 树
#   lead_npe_run2.sh npe2            跑完整流程
#   lead_npe_run2.sh npe2 restore    只把 api29-root 指回 r63
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
REPO=/media/psf/Home/WorkSpace/saidroid-next
RUN=${1:-npe2}
COMP=/var/tmp/saidroid-next-api29-component-r66
EVID=$REPO/build/evidence/$RUN
BASE=/home/art/releases/api29-20261026-r63

restore_base() {
  $SSH "python3 -c \"import os,pathlib;link=pathlib.Path('/home/art/api29-root');tmp=pathlib.Path('/home/art/.api29-root-lead');tmp.unlink(missing_ok=True);tmp.symlink_to('$BASE');os.replace(tmp,link);print('ROOT_NOW='+os.readlink(link))\""
}
if [ "${2:-}" = "restore" ]; then restore_base; exit $?; fi

cd "$REPO" || exit 1
scripts/devlock.sh status | grep -q "lead-npe" || { echo "LOCK_NOT_MINE"; exit 2; }
mkdir -p "$EVID"

echo "=== 0. 关掉所有 owned 进程（deploy 前置条件）==="
scripts/lead_close_all.sh 2>&1 | tail -2

echo "=== 1. 安装 r64 ==="
python3 scripts/api29/deploy-component.py "$COMP" "$RUN" 2>&1 | tail -2
if ! sshpass -e ssh -o StrictHostKeyChecking=no "$H" "readlink /home/art/api29-root | grep -q $RUN"; then
  echo "DEPLOY_OR_ROOT_FAILED"; echo "ROOT=$(sshpass -e ssh -o StrictHostKeyChecking=no $H 'readlink /home/art/api29-root')"; exit 3
fi
echo "ROOT=ok"

echo "=== 2. 带 stderr 诊断启动 QQ ==="
scripts/sd.sh launch --wait 45 --env SAILDROID_ANDROID_LOG_STDERR=1 | tail -2
scripts/sd.sh wait --wait 60 --marker 'SDWINDOW_SESSION=drawn' | tail -1
sleep 4
scripts/sd.sh shot "$RUN-login" | tail -1

echo "=== 3. 点「登录」(791,1985) ==="
scripts/sd.sh input tap 791 1985 60 | tail -1
sleep 5
scripts/sd.sh shot "$RUN-after-login" | tail -1

echo "=== 4. 若出现短信验证 H5 / QQBrowserActivity，再点继续 ==="
scripts/sd.sh input tap 540 1900 60 | tail -1
sleep 6
scripts/sd.sh shot "$RUN-after-second-tap" | tail -1

echo "=== 5. 等崩溃标记 ==="
scripts/sd.sh wait --wait 20 --marker 'SDRUNTIME=failed' | tail -1

echo "=== 6. 日志 ==="
scripts/sd.sh log -n 4000 > "$EVID/app.log" 2>&1
echo "LOG_LINES=$(wc -l < "$EVID/app.log")"
echo "SDVIEWS_LINES=$(grep -ac 'SDVIEWS=' "$EVID/app.log" || true)"
echo "NPE_COUNT=$(grep -ac 'MarginLayoutParams' "$EVID/app.log" || true)"
echo "WEBVIEW_EVENTS=$(grep -ac 'SDWEBVIEW=' "$EVID/app.log" || true)"
echo "ACTIVITIES=$(grep -ao 'SDACTIVITY=launched|class=[^|]*' "$EVID/app.log" | tail -4 | tr '\n' ' ')"

echo "=== 7. 关闭并恢复基线 ==="
scripts/sd.sh close | tail -1
restore_base

echo "=== 8. View 树（若抓到）==="
grep -a 'SDVIEWS=' "$EVID/app.log" | head -100
