#!/bin/bash
# Lead 的 NPE 崩溃现场诊断窗口：装 diag2（r63 同一套输入 + SdViewDump），
# 带 stderr 诊断跑一次 QQ，把 View 树 dump 抓回来。
#
#   lead_npe_run.sh npe1            完整跑（需要已持有锁 lead-npe）
#   lead_npe_run.sh npe1 restore    只把 api29-root 指回 r63
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=8"
REPO=/media/psf/Home/WorkSpace/saidroid-next
RUN=${1:-npe1}
COMP=/var/tmp/saidroid-next-api29-component-r64
EVID=$REPO/build/evidence/$RUN
BASE=/home/art/releases/api29-20261026-r63

restore_base() {
  $SSH "python3 -c \"import os,pathlib;link=pathlib.Path('/home/art/api29-root');assert link.is_symlink();tmp=pathlib.Path('/home/art/.api29-root-lead');tmp.unlink(missing_ok=True);tmp.symlink_to('$BASE');os.replace(tmp,link);print('ROOT_NOW='+os.readlink(link))\""
}

if [ "${2:-}" = "restore" ]; then restore_base; exit $?; fi

cd "$REPO" || exit 1
scripts/devlock.sh status | grep -q "lead-npe" || { echo "LOCK_NOT_MINE"; exit 2; }
mkdir -p "$EVID"

echo "=== 1. 安装 diag2 组件 ==="
python3 scripts/api29/deploy-component.py "$COMP" "$RUN" 2>&1 | tail -3 || { echo DEPLOY_FAILED; exit 3; }

echo "=== 2. 带诊断启动 QQ ==="
scripts/sd.sh launch --wait 45 --env SAILDROID_ANDROID_LOG_STDERR=1 | tail -3

echo "=== 3. 等窗口/等崩溃 ==="
scripts/sd.sh wait --wait 50 --marker 'SDWINDOW_SESSION=drawn' | tail -2
scripts/sd.sh wait --wait 25 --marker 'SDRUNTIME=failed' | tail -2

echo "=== 4. 截图 ==="
scripts/sd.sh shot "$RUN-qq" | tail -2

echo "=== 5. 日志 ==="
scripts/sd.sh log -n 3000 > "$EVID/app.log" 2>&1
echo "LOG_LINES=$(wc -l < "$EVID/app.log")"
echo "SDVIEWS_LINES=$(grep -c 'SDVIEWS=' "$EVID/app.log" || true)"
echo "NPE_COUNT=$(grep -c 'MarginLayoutParams' "$EVID/app.log" || true)"

echo "=== 6. 关闭并恢复基线 ==="
scripts/sd.sh close | tail -2
restore_base

echo "=== 7. View 树（若抓到）==="
grep 'SDVIEWS=' "$EVID/app.log" | head -80
