#!/bin/bash
# lipstick SIGSEGV 三分法（2026-10-27）
#
# 背景：lipstick 在 05:15:54 与 06:54:38 各崩一次（sig=11，无 reboot，systemd 自动拉起），
# 第二次崩溃前 1 秒是 `evdevtouch: Could not read from input device`，而 dmesg 里
# sdinput 设备的创建节奏正好等于我们每次 sd.sh input 的节奏。crash dump 被 Sailfish
# 的隐私提示挡住（`rich-core: privacy notice not accepted`），拿不到 backtrace。
#
# 所以只能用「分离变量」的办法问三个问题：
#   A 只截图、不注入、不跑应用      -> 崩 = 读回/HWC2 截图路径
#   B 只建/销 uinput 设备、不发事件  -> 崩 = 热插拔 churn（evdevtouch）
#   C 只跑我们的窗口、不注入不截图   -> 崩 = 我们自己的 wl_surface/wl_shm 用法
#
# 每臂之间对比 lipstick pid；任何一臂崩了，后面的臂照跑（每次崩溃约 8 秒自愈），
# 最后一次性给判定。脚本自己拿锁、自己放锁、退出时恢复 api29-root。
#
# 用法：bash scripts/lead_lipstick_bisect.sh <run-label>
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=8"
REPO=/media/psf/Home/WorkSpace/saidroid-next
LABEL=${1:-bisect1}
OUT="$REPO/build/evidence/$LABEL"
ROOT_LINK=/home/art/api29-root
RESTORE=${RESTORE:-/home/art/releases/api29-r63}
mkdir -p "$OUT"

have_lock=0
cleanup() {
  $SSH "/home/art/bin/saildroid-open --package com.tencent.mobileqq --close" >/dev/null 2>&1
  if [ -n "${root_before:-}" ]; then
    $SSH "python3 -c \"import os,tempfile;d=os.path.dirname('$ROOT_LINK');l=os.path.join(d,'.api29-root.tmp');os.symlink('$root_before',l) if not os.path.lexists(l) else None;os.replace(l,'$ROOT_LINK')\"" >/dev/null 2>&1
  fi
  if [ "$have_lock" = 1 ]; then
    bash "$REPO/scripts/devlock.sh" release "$LABEL" 2>&1 | tail -1
  fi
}
trap cleanup EXIT

# 设备上 `pgrep -x lipstick` 实测返回空、`pidof lipstick` 正常（2026-10-27 实测），
# 用 pidof；同时取 /proc/<pid>/stat 第 22 字段 start_ticks —— pid 会复用，ticks 不会。
pid_now() { $SSH "pidof lipstick | cut -d' ' -f1" 2>/dev/null | tr -d '\r'; }
ticks_now() { local p; p=$(pid_now); [ -n "$p" ] && $SSH "awk '{print \$22}' /proc/$p/stat" 2>/dev/null | tr -d '\r' || true; }

bash "$REPO/scripts/lead_close_all.sh" >/dev/null 2>&1
root_before=$($SSH "readlink -f $ROOT_LINK" 2>/dev/null | tr -d '\r')
echo "ROOT_BEFORE=$root_before"

bash "$REPO/scripts/devlock.sh" acquire 600 "$LABEL" 2>&1 | tail -1 || true
if [ "$(bash "$REPO/scripts/devlock.sh" status 2>&1 | grep -c "by: $LABEL")" = "1" ]; then have_lock=1; fi
echo "LOCK_OWNED=$have_lock"

P0=$(pid_now)
echo "LIPSTICK_BEFORE=$P0"
$SSH "dmesg | tail -40" > "$OUT/dmesg-before.txt" 2>&1
$SSH "journalctl --no-pager -o short-iso -S '-5 min' | tail -60" > "$OUT/journal-before.txt" 2>&1

# 先把带 serve/hold 的新注入器推上去（sd.sh 会按 sha 比对并重编）。
banner() { echo; echo "########## $1 ##########"; }
banner "PUSH injector"
bash "$REPO/scripts/sd.sh" inputhold 100 2>&1 | tail -3

# ---------- A：只截图 ----------
banner "ARM_A screenshot_only"
A0=$(pid_now); A0T=$(ticks_now)
for i in $(seq 1 12); do
  $SSH "python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot bisectA$i" >/dev/null 2>&1
  sleep 1
done
sleep 3
A1=$(pid_now); A1T=$(ticks_now)
echo "ARM_A|lipstick_before=$A0|ticks=$A0T|after=$A1|ticks=$A1T|survived=$([ -n "$A0" ] && [ "$A0" = "$A1" ] && echo yes || echo NO)"

# ---------- B：只建/销设备，不发事件 ----------
banner "ARM_B uinput_churn_only"
B0=$(pid_now); B0T=$(ticks_now)
for i in $(seq 1 10); do
  $SSH "/home/art/bin/sdinput hold 300" >/dev/null 2>&1
  sleep 0.7
done
sleep 3
B1=$(pid_now); B1T=$(ticks_now)
echo "ARM_B|lipstick_before=$B0|ticks=$B0T|after=$B1|ticks=$B1T|survived=$([ -n "$B0" ] && [ "$B0" = "$B1" ] && echo yes || echo NO)"

# ---------- C：只跑我们的窗口 ----------
banner "ARM_C app_window_only"
C0=$(pid_now); C0T=$(ticks_now)
$SSH "/home/art/bin/saildroid-open --package com.tencent.mobileqq" >/dev/null 2>&1
sleep 45
C1=$(pid_now); C1T=$(ticks_now)
$SSH "/home/art/bin/sdtool.py --package com.tencent.mobileqq status" > "$OUT/arm-c-status.txt" 2>&1
$SSH "/home/art/bin/saildroid-open --package com.tencent.mobileqq --close" >/dev/null 2>&1
sleep 2
C2=$(pid_now); C2T=$(ticks_now)
echo "ARM_C|lipstick_before=$C0|ticks=$C0T|after=$C1|ticks=$C1T|after_close=$C2|ticks=$C2T|survived=$([ -n "$C0" ] && [ "$C0" = "$C1" ] && echo yes || echo NO)"

# ---------- 汇总 ----------
banner "SUMMARY"
$SSH "dmesg | tail -60" > "$OUT/dmesg-after.txt" 2>&1
$SSH "journalctl --no-pager -o short-iso -S '-10 min' | grep -E 'lipstick|evdevtouch|ANOM_ABEND|restart' | tail -40" > "$OUT/journal-after.txt" 2>&1
PFINAL=$(pid_now); PFINALT=$(ticks_now)
echo "LIPSTICK_FINAL=$PFINAL|ticks=$PFINALT"
if [ -z "$P0" ]; then echo "BISECT_INVALID|reason=lipstick_pid_not_detected"; fi
echo "LIPSTICK_CHANGED=$([ "$P0" = "$PFINAL" ] && echo no || echo YES)"
echo "--- journal 里崩溃证据 ---"
grep -c "ANOM_ABEND" "$OUT/journal-after.txt" 2>/dev/null | sed 's/^/ANOM_ABEND_COUNT=/'
grep -c "evdevtouch" "$OUT/journal-after.txt" 2>/dev/null | sed 's/^/EVDEVTOUCH_COUNT=/'
echo "EVIDENCE_DIR=$OUT"
$SSH "cat /home/art/test/.device-lock/owner 2>/dev/null" >/dev/null 2>&1
